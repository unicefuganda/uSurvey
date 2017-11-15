from django import forms
from django.forms import ModelForm
import re
from django.core.exceptions import ValidationError
from django.conf import settings
from survey.models import Question, BatchQuestion, QuestionSet
from survey.models import (QuestionOption, Batch, Answer, QuestionModule, MultiChoiceAnswer, MultiSelectAnswer,
                           QuestionFlow, AnswerAccessDefinition, ResponseValidation, DateAnswer, TextAnswer,
                           NumericalAnswer, AutoResponse, SurveyParameterList)
from survey.forms.form_helper import FormOrderMixin, Icons


class ValidationField(forms.ModelChoiceField, Icons):
    pass


def get_question_form(model_class):

    class QuestionForm(ModelForm, FormOrderMixin):
        VALIDATION_ANSWER_TYPES = [DateAnswer.choice_name(), TextAnswer.choice_name(),
                                   NumericalAnswer.choice_name(), AutoResponse.choice_name()]
        options = forms.CharField(max_length=50, widget=forms.HiddenInput(), required=False)
        response_validation = ValidationField(queryset=ResponseValidation.objects.all(), required=False)

        def __init__(
                self,
                qset,
                data=None,
                initial=None,
                parent_question=None,
                instance=None,
                prev_question=None):
            super(QuestionForm, self).__init__(
                data=data, initial=initial, instance=instance)
            self.fields['identifier'].label = "Variable name"
            self.fields['qset'].widget = forms.HiddenInput()
            self.fields['qset'].initial = qset.pk
            self.qset = qset
            self.prev_question = prev_question
            # depending on type of ussd/odk access of qset restrict the answer
            # type
            self.fields['answer_type'].choices = [
                choice for choice in self.fields['answer_type'].choices if choice[0] in qset.answer_types]
            self.fields['answer_type'].choices.insert(
                0, ('', '----Select Answer Type----'))
            if instance:
                self.help_text = ' and '.join(AnswerAccessDefinition.access_channels(instance.answer_type))
                self.fields['answer_type'].help_text = self.help_text
            self.answer_map = {}
            definitions = AnswerAccessDefinition.objects.all()
            for defi in definitions:
                self.answer_map[defi.answer_type] = self.answer_map.get(defi.answer_type, [])
                self.answer_map[defi.answer_type].append(defi.channel)
            self.fields['response_validation'].icons = {'add': {'data-toggle': "modal",
                                                                 'data-target': "#add_validation",
                                                                 'id': 'add_validation_button',
                                                                 'title': 'Add Validation'},
                                                        }
            self.parent_question = parent_question
            self.order_fields(['module', 'group', 'identifier',
                               'text', 'answer_type', 'mandatory'])

        class Meta:
            model = model_class
            exclude = []
            widgets = {
                'text': forms.Textarea(
                    attrs={
                        "rows": 5,
                        "cols": 30,
                        "maxlength": "150",
                    }),
            }

        def clean_group(self):
            group = self.cleaned_data['group']
            if group:
                qset = QuestionSet.get(id=self.qset.pk)
                identifiers = group.parameter_questions().values_list('identifier', flat=True)
                existing_identifiers = Question.objects.filter(identifier__in=identifiers,
                                                               qset__pk=self.qset.pk).values_list('identifier', flat=True)
                if existing_identifiers.exists():
                    raise ValidationError(
                        '%s already exist in this %s. '
                        'Consider creating a question with modified identifier name and using skip logic in your %s' %
                        (','.join(existing_identifiers), qset.verbose_name(), qset.verbose_name()))
                if hasattr(qset, 'survey') and qset.survey.listing_form:
                    existing_identifiers = qset.survey.listing_form.questions.filter(identifier__in=identifiers
                                                                                     ).values_list('identifier',
                                                                                                   flat=True)
                    if existing_identifiers.exists():
                        raise ValidationError(
                            '%s already exist as a listing question for this %s. '
                            'Consider creating a question with modified identifier name and using skip logic in your %s' %
                            (','.join(existing_identifiers), qset.verbose_name(), qset.verbose_name()))
            return group

        def clean_options(self):
            options = dict(self.data).get('options')
            if options:
                options = filter(lambda text: text.strip(), options)
                # options = map(lambda option: re.sub("[%s]" % settings.USSD_IGNORED_CHARACTERS, '', option), options)
                options = map(
                    lambda option: re.sub(
                        "  ", ' ', option), options)
                options = map(lambda option: option.strip(), options)
                self.cleaned_data['options'] = options
            return options

        def clean_identifier(self):
            identifier = self.cleaned_data['identifier']
            pattern = '^[a-zA-Z][0-9a-zA-Z_]+$'
            if re.match(pattern, identifier) is None:
                raise ValidationError(
                    'Identifier must start with a letter, and must contain alphanumeric values or _')
            if Question.objects.filter(
                    identifier__iexact=identifier,
                    qset__pk=self.qset.pk).exists():
                if self.instance and self.instance.identifier == identifier:
                    pass
                else:
                    raise ValidationError(
                        '%s already in use for this %s' %
                        (identifier, model_class.type_name()))
            # if this is a batch question also check if there are parameter
            # questions with this name
            qset = QuestionSet.get(id=self.qset.pk)
            if hasattr(
                    qset,
                    'parameter_list') and qset.parameter_list and qset.parameter_list.parameters.filter(
                    identifier__iexact=identifier).exists():
                raise ValidationError(
                    '%s is already in captured as a group parameter for this %s' %
                    (identifier, qset.verbose_name()))
            # for sampled surveys, check if this is already implemented in listing
            if hasattr(qset, 'survey') and qset.survey.listing_form and qset.survey.listing_form.questions.filter(
                    identifier__iexact=identifier).exists():
                raise ValidationError(
                    '%s is already in captured as a listing question for this %s' %
                    (identifier, qset.verbose_name()))
            return self.cleaned_data['identifier']

        def clean_text(self):
            """Make sure any field referenced here belongs to same batch. Field refs are denoted by {{.+}} brackets
            :return:
            """
            pattern = '{{ *([0-9a-zA-Z_]+) *}}'
            label = self.data.get('text', '')
            requested_identifiers = re.findall(pattern, label)
            if requested_identifiers:
                ids = self.qset.questions.filter(
                    identifier__in=requested_identifiers).values_list(
                    'identifier', flat=True)
                ids = list(ids)
                if len(set(ids)) != len(set(requested_identifiers)):
                    raise ValidationError(
                        '%s is not in %s' %
                        (', '.join(
                            set(requested_identifiers).difference(ids)),
                            self.qset.name))
            return self.cleaned_data['text']

        def clean(self):
            answer_type = self.cleaned_data.get('answer_type', None)
            options = self.cleaned_data.get('options', None)
            response_validation = self.cleaned_data.get('response_validation', None)
            text = self.cleaned_data.get('text', None)
            self._check__multichoice_and_options_compatibility(
                answer_type, options)
            self._strip_special_characters_for_ussd(text)
            self._prevent_duplicate_subquestions(text)
            if answer_type:
                answer_class = Answer.get_class(answer_type)
                validator_names = [validator.__name__ for validator in answer_class.validators()]
                if response_validation and response_validation.validation_test not in validator_names:
                    raise ValidationError('Selected Validation is not compatible with chosen answer type')
            return self.cleaned_data

        def _check__multichoice_and_options_compatibility(
                self, answer_type, options):
            if answer_type in [
                    MultiChoiceAnswer.choice_name(),
                    MultiSelectAnswer.choice_name()] and not options:
                message = 'Question Options missing.'
                self._errors['answer_type'] = self.error_class([message])
                del self.cleaned_data['answer_type']

            if answer_type not in [
                    MultiChoiceAnswer.choice_name(),
                    MultiSelectAnswer.choice_name()] and options:
                del self.cleaned_data['options']

        def _strip_special_characters_for_ussd(self, text):
            if text:
                text = re.sub(
                    "[%s]" %
                    settings.USSD_IGNORED_CHARACTERS,
                    '',
                    text)
                self.cleaned_data['text'] = re.sub("  ", ' ', text)

        def _prevent_duplicate_subquestions(self, text):
            if self.parent_question:
                duplicate_sub_question = self.parent_question.get_subquestions().filter(text__iexact=text)
                has_instance_id_different = (
                    self.instance.id and self.instance.id != duplicate_sub_question[0].id)

                if duplicate_sub_question.exists() and (
                        not self.instance.id or has_instance_id_different):
                    self._errors['text'] = self.error_class(
                        ["Sub question for this question with this text already exists."])
                    del self.cleaned_data['text']

        def kwargs_has_batch(self, **kwargs):
            return 'qset' in kwargs and isinstance(kwargs['qset'], Batch)

        def options_supplied(self, commit):
            return commit and self.cleaned_data.get('options', None)

        def save_question_options(self, question):
            order = 0
            options = self.cleaned_data['options']
            question.options.all().delete()
            # options.sort()
            for text in options:
                order += 1
                QuestionOption.objects.create(
                    question=question, text=text, order=order)

        def save(self, commit=True, zombie=False, **kwargs):
            question = super(QuestionForm, self).save(commit=False)
            qset = question.qset
            if commit:
                if question.pk is None:
                    question.save()
                    # get the last question inline
                    # create a inline flow with current qset
                    qset = question.qset
                    # qset = QuestionSet.get(id=qset.id)
                    if self.prev_question:
                        last_question = self.prev_question
                    else:
                        last_question = qset.last_question_inline()
                    if last_question:
                        if zombie is False:
                            # incase, inline flow with no next quest already
                            # exists
                            flow, _ = QuestionFlow.objects.get_or_create(
                                question=last_question, validation__isnull=True)
                            prev_next_question = flow.next_question
                            flow.next_question = question
                            flow.save()
                            # now connect present question back to the flow
                            QuestionFlow.objects.create(
                                question=question, next_question=prev_next_question)
                    elif qset.start_question is None:
                        qset.start_question = question
                        qset.save()
                else:
                    question.save()
                if hasattr(qset, 'survey'):     # basicallyy check for Batch scenario
                    SurveyParameterList.update_parameter_list(qset)

                # self.qset.questions_inline.invalidate()
            if self.options_supplied(commit):
                self.save_question_options(question)
            return question

    return QuestionForm


QuestionForm = get_question_form(Question)
BatchQuestionForm = get_question_form(BatchQuestion)

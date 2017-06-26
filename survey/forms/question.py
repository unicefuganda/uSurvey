from django import forms
from django.forms import ModelForm
import re
from django.core.exceptions import ValidationError
from django.conf import settings
from survey.models import Question, BatchQuestion, QuestionSet
from survey.models import (QuestionOption, Batch, Answer, QuestionModule, MultiChoiceAnswer, MultiSelectAnswer,
                           QuestionFlow, AnswerAccessDefinition, ResponseValidation)
from survey.forms.form_helper import FormOrderMixin


def get_question_form(model_class):

    class QuestionForm(ModelForm, FormOrderMixin):
        # prev_question = forms.CharField(
        #     max_length=50, widget=forms.HiddenInput(), required=False)
        options = forms.CharField(
            max_length=50, widget=forms.HiddenInput(), required=False)

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
            # if prev_question:
            #     self.fields['prev_question'].initial = prev_question.pk
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
                answer_class = Answer.get_class(instance.answer_type)
                validator_names = [validator.__name__ for validator in answer_class.validators()]
                self.fields['response_validation'].queryset = ResponseValidation.objects.filter(validation_test__in=
                                                                                                validator_names)
            self.answer_map = {}
            definitions = AnswerAccessDefinition.objects.all()
            for defi in definitions:
                self.answer_map[defi.answer_type] = self.answer_map.get(defi.answer_type, [])
                self.answer_map[defi.answer_type].append(defi.channel)
            # group_choices = sorted([each for each in self.fields['group'].choices if each[0]!= ''],
            #                        key=lambda tup: (tup[0]))
            # group_choices.insert(0,('', '-----Select Group----'))
            # self.fields['group'].choices = group_choices
            #
            # module_choices = sorted([each for each in self.fields['module'].choices if each[0]!=''], key=lambda tup: (tup[1]))
            # module_choices.insert(0,('','-----Select Module----'))
            # self.fields['module'].choices = module_choices

            self.fields[
                'text'].help_text = "To get previous identifier suggestions, type {{ any time"
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
                    (identifier, model_class.type_name()))
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
            text = self.cleaned_data.get('text', None)
            self._check__multichoice_and_options_compatibility(
                answer_type, options)
            self._strip_special_characters_for_ussd(text)
            self._prevent_duplicate_subquestions(text)
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
            if commit:
                if question.pk is None:
                    question.save()
                    # get the last question inline
                    # create a inline flow with current qset
                    qset = question.qset
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
                # self.qset.questions_inline.invalidate()
            if self.options_supplied(commit):
                self.save_question_options(question)
            return question

    return QuestionForm


QuestionForm = get_question_form(Question)
BatchQuestionForm = get_question_form(BatchQuestion)

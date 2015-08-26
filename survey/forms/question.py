from django import forms
from django.forms import ModelForm
import re
from survey.models import Question, QuestionOption, Batch, Answer, QuestionModule, \
            HouseholdMemberGroup, MultiChoiceAnswer, MultiSelectAnswer, QuestionFlow
from django.conf import settings


class QuestionForm(ModelForm):

    options = forms.CharField(max_length=50, widget=forms.HiddenInput(), required=False)

    def __init__(self, batch, data=None, initial=None, parent_question=None, instance=None):
        super(QuestionForm, self).__init__(data=data, initial=initial, instance=instance)
        self.fields['answer_type'].choices = list(Question.ANSWER_TYPES)
        self.fields['module'].choices = map(lambda question_module: (question_module.id, question_module.name), QuestionModule.objects.filter())
        self.fields['identifier'].label = "Variable name"
        self.fields['batch'].widget = forms.HiddenInput()
        self.fields['batch'].initial = batch.pk
        self.parent_question = parent_question
        self.parent_has_module = False
        self.parent_has_group = False
        self._set_group_choices()
        self._set_module_choices()

    def _set_group_choices(self):
        groups = []
        if self.parent_question and self.parent_question.group:
            groups = [self.parent_question.group]
            self.parent_has_group = True
        if not self.parent_question:
            groups = HouseholdMemberGroup.objects.all()
        self.fields['group'].choices = [(group.id, group.name) for group in groups]

    def _set_module_choices(self):
        if self.parent_question and self.parent_question.module:
            modules = [self.parent_question.module]
            self.parent_has_module = True
        else:
            modules = QuestionModule.objects.filter()
        self.fields['module'].choices = [(question_module.id, question_module.name) for question_module in modules]

    class Meta:
        model = Question
        fields =['batch', 'module', 'text', 'identifier', 'group', 'answer_type']

        widgets ={
            'text': forms.Textarea(attrs={"rows":4, "cols":100,"maxlength":"150"}),
            'module': forms.Select(choices=[])
        }

    def clean_options(self):
        options = dict(self.data).get('options')
        if options:
            options = filter(lambda text: text.strip(), options)
            options = map(lambda option: re.sub("[%s]" % settings.USSD_IGNORED_CHARACTERS, '', option), options)
            options = map(lambda option: re.sub("  ", ' ', option), options)
            self.cleaned_data['options'] = options
        return options

    def clean_module(self):
        module = self.cleaned_data.get('module', None)
        if module and self.parent_has_module and module.id != self.parent_question.module.id:
            message = "Subquestions cannot have a different module from its parent."
            self._errors['module'] = self.error_class([message])
            del self.cleaned_data['module']
        return module

    def clean_group(self):
        group = self.cleaned_data.get('group', None)
        if group and self.parent_has_group and group.id != self.parent_question.group.id:
            message = "Subquestions cannot have a different group from its parent."
            self._errors['group'] = self.error_class([message])
            del self.cleaned_data['group']
        return group

    def clean(self):
        answer_type = self.cleaned_data.get('answer_type', None)
        options = self.cleaned_data.get('options', None)
        text = self.cleaned_data.get('text', None)
        self._check__multichoice_and_options_compatibility(answer_type, options)
        self._strip_special_characters_for_ussd(text)
        self._prevent_duplicate_subquestions(text)
        return self.cleaned_data

    def _check__multichoice_and_options_compatibility(self, answer_type, options):
        if answer_type in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer.choice_name()] and not options:
            message = 'Question Options missing.'
            self._errors['answer_type'] = self.error_class([message])
            del self.cleaned_data['answer_type']

        if answer_type not in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer.choice_name()] and options:
            del self.cleaned_data['options']

    def _strip_special_characters_for_ussd(self, text):
        if text:
            text = re.sub("[%s]" % settings.USSD_IGNORED_CHARACTERS, '', text)
            self.cleaned_data['text'] = re.sub("  ", ' ', text)

    def _prevent_duplicate_subquestions(self, text):
        if self.parent_question:
            duplicate_sub_question = self.parent_question.get_subquestions().filter(text__iexact=text)
            has_instance_id_different = (self.instance.id and self.instance.id != duplicate_sub_question[0].id)

            if duplicate_sub_question.exists() and (not self.instance.id or has_instance_id_different):
                self._errors['text'] = self.error_class(["Sub question for this question with this text already exists."])
                del self.cleaned_data['text']

    def kwargs_has_batch(self, **kwargs):
        return kwargs.has_key('batch') and isinstance(kwargs['batch'], Batch)

    def options_supplied(self, commit):
        return commit and self.cleaned_data.get('options', None)

    def save_question_options(self, question):
        order = 0
        options = self.cleaned_data['options']
        question.options.all().delete()
        for text in options:
            order += 1
            QuestionOption.objects.create(question=question, text=text, order=order)

    def save(self, commit=True, **kwargs):
        question = super(QuestionForm, self).save(commit=False)
        if commit:
            if question.pk is None:
                question.save()
                #get the last question inline
                #create a inline flow with current batch
                batch = question.batch
                last_question = batch.last_question_inline()
                if last_question:
                    QuestionFlow.objects.get_or_create(question=last_question, next_question=question)
                else:
                    batch.start_question = question
                    batch.save()
            else:
                question.save()
        if self.options_supplied(commit):
            self.save_question_options(question)
        return question
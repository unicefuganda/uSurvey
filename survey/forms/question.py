from django import forms
from django.forms import ModelForm
import re
from survey.models import QuestionModule

from survey.models.batch import Batch
from survey.models.question import Question, QuestionOption
from survey.models.householdgroups import HouseholdMemberGroup

class QuestionForm(ModelForm):

    options = forms.CharField(max_length=50, widget=forms.HiddenInput(), required=False)

    def __init__(self,data=None, initial=None, parent_question=None ,instance=None):
        super(QuestionForm, self).__init__(data=data,initial=initial,instance=instance)
        self.fields['answer_type'].choices = list(Question.TYPE_OF_ANSWERS)
        self.fields['module'].choices = map(lambda question_module: (question_module.id, question_module.name), QuestionModule.objects.filter())

        groups = []

        if parent_question and parent_question.group:
            groups = [parent_question.group]

        if not parent_question:
            groups = HouseholdMemberGroup.objects.all()

        self.fields['group'].choices = [(group.id, group.name) for group in groups]
        self.parent_question = parent_question

    class Meta:
        model = Question
        fields =['module', 'text', 'group', 'answer_type']

        widgets ={
            'text': forms.Textarea(attrs={"rows":4, "cols":100,"maxlength":"150"}),
            'module': forms.Select(choices=QuestionModule.objects.filter())
        }

    def clean_options(self):
        options = dict(self.data).get('options')
        if options:
          options = filter(lambda text: text.strip(), options)
          options = map(lambda option: re.sub("[%s]" % Question.IGNORED_CHARACTERS, '', option), options)
          options = map(lambda option: re.sub("  ", ' ', option), options)
          self.cleaned_data['options'] = options
        return options

    def clean(self):
        answer_type = self.cleaned_data.get('answer_type', None)
        options = self.cleaned_data.get('options', None)
        text = self.cleaned_data.get('text', None)

        if answer_type==Question.MULTICHOICE and not options:
            message = 'Question Options missing.'
            self._errors['answer_type'] = self.error_class([message])
            del self.cleaned_data['answer_type']

        if answer_type != Question.MULTICHOICE and options:
            del self.cleaned_data['options']

        if text:
            text = re.sub("[%s]" % Question.IGNORED_CHARACTERS, '', text)
            self.cleaned_data['text'] = re.sub("  ", ' ', text)

        if self.parent_question:
            duplicate_sub_question = self.parent_question.get_subquestions().filter(text__iexact=text)
            if duplicate_sub_question.exists():
                self._errors['text'] = self.error_class(["Sub question for this question with this text already exists."])

        return self.cleaned_data

    def kwargs_has_batch(self, **kwargs):
        return kwargs.has_key('batch') and isinstance(kwargs['batch'], Batch)

    def options_supplied(self, commit):
        return commit and self.cleaned_data.get('options', None)

    def save_question_options(self, question):
        order = 0
        options = self.cleaned_data['options']
        for text in options:
            order += 1
            option, bbb = QuestionOption.objects.get_or_create(question=question, text=text)
            option.order = order
            option.save()

    def save(self, commit=True, **kwargs):
        question = super(QuestionForm, self).save(commit=False)
        if commit:
            maximum_order = HouseholdMemberGroup.objects.get(id=kwargs['group'][0]).maximum_question_order()
            order = maximum_order + 1 if maximum_order else 1
            question.order = order
            question.save()

        if self.kwargs_has_batch(**kwargs):
            question.batches.add(kwargs['batch'])

        if self.options_supplied(commit):
            self.save_question_options(question)

        return question
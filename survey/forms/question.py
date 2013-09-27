from django import forms
from django.forms import ModelForm

from survey.models.batch import Batch
from survey.models.question import Question, QuestionOption
from survey.models.householdgroups import HouseholdMemberGroup

class QuestionForm(ModelForm):

    options = forms.CharField(max_length=50, widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['answer_type'].choices = list(Question.TYPE_OF_ANSWERS)
        self.fields['group'].choices = [(group.id, group.name) for group in HouseholdMemberGroup.objects.all()]

    class Meta:
        model = Question
        fields =['text', 'group', 'answer_type']

        widgets ={
            'text': forms.Textarea(attrs={"rows":4, "cols":50})
        }

    def clean_options(self):
        options = dict(self.data).get('options')
        if options:
          options = filter(lambda text: text.strip(), options)
          self.cleaned_data['options'] = options          
        return options

    def clean(self):
        answer_type = self.cleaned_data.get('answer_type', None)
        options = self.cleaned_data.get('options', None)

        if answer_type==Question.MULTICHOICE and not options:
            message = 'Question Options missing.'
            self._errors['answer_type'] = self.error_class([message])
            del self.cleaned_data['answer_type']

        if answer_type != Question.MULTICHOICE and options:
            del self.cleaned_data['options']

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
        if self.kwargs_has_batch(**kwargs):
            question.batch = kwargs['batch']
        if commit:
            maximum_order = HouseholdMemberGroup.objects.get(id=kwargs['group'][0]).maximum_question_order()
            order = maximum_order + 1 if maximum_order else 1
            question.order = order
            question.save()

        if self.options_supplied(commit):
            self.save_question_options(question)

        return question
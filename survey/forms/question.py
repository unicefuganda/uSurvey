from django import forms
from django.forms import ModelForm

from survey.models.question import Question
from survey.models.householdgroups import HouseholdMemberGroup

class QuestionForm(ModelForm):

    options = forms.CharField(max_length=50, widget=forms.HiddenInput())

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

    def clean(self):
        answer_type = self.cleaned_data.get('answer_type', None)
        options = self.cleaned_data.get('options', None)

        if answer_type==Question.MULTICHOICE and not options:
            message = 'Question Options missing.'
            self._errors['answer_type'] = self.error_class([message])
            del self.cleaned_data['answer_type']

        return self.cleaned_data


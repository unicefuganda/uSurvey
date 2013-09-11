from django.forms import ModelForm
from django import forms
from survey.models.surveys import Survey
from survey.models.question import Question

class SurveyForm(ModelForm):
    questions = forms.ModelMultipleChoiceField(label=u'Questions', queryset=Question.objects.all(),
                                                widget=forms.SelectMultiple(attrs={'class': 'multi-select'}))

    class Meta:
        model = Survey
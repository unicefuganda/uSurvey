from django.forms import ModelForm
from django import forms
from survey.models.surveys import Survey
from survey.models.question import Question

class SurveyForm(ModelForm):

    class Meta:
        model = Survey
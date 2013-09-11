from django.forms import ModelForm
from django import forms
from survey.models.surveys import Survey

class SurveyForm(ModelForm):

    class Meta:
        model = Survey

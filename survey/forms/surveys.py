from django.forms import ModelForm
from django import forms
from survey.models.surveys import Survey
from survey.models.question import Question

class SurveyForm(ModelForm):

    class Meta:
        model = Survey
        fields=['name', 'description', 'type', 'sample_size']
        widgets={
            'type':forms.RadioSelect(choices=[(True, 'Aggregate'), ( False, 'Roster')]),
        }
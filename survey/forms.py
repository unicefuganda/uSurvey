from django import forms
from survey.models import *
from django.forms import ModelForm

class InvestigatorForm(ModelForm):
    class Meta:
        model = Investigator
        fields = ['name', 'mobile_number','age', 'level_of_education', 'location', 'male', 'language']
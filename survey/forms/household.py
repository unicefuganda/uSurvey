from django import forms
from survey.models_file import *
from django.forms import ModelForm

class HouseholdForm(ModelForm):

    class Meta:
        model = Household
        exclude = ['investigator']
        widgets = {
        'number_of_males':forms.TextInput(attrs={'class':"small-positive-number" }),
        'number_of_females':forms.TextInput(attrs={'class':"small-positive-number" }),
        }

from django import forms
from survey.models import *
from django.forms import ModelForm

class HouseholdForm(ModelForm):

    class Meta:
        model = Household
        exclude = ['investigator']
        widgets = {
        'number_of_males':forms.TextInput(attrs={'class':"small-positive-number", 'type':'number' }),
        'number_of_females':forms.TextInput(attrs={'class':"small-positive-number", 'type':'number' }),
        }

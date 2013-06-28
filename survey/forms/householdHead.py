from django import forms
from survey.models import *
from django.forms import ModelForm
from django.core.validators import *
from survey.investigator_configs import OCCUPATION
from widgets import InlineRadioSelect

class HouseholdHeadForm(ModelForm):

    class Meta:
        model = HouseholdHead
        exclude = ['household']
        widgets = {
            'surname': forms.TextInput(attrs={'placeholder': 'Name'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'male': InlineRadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'age': forms.TextInput(attrs={'placeholder': 'Age', 'min':10, 'max':99, 'type':'number' }),
            'resident_since':forms.TextInput(attrs={'min':0, 'type':'number' }),
            'time_measure': forms.HiddenInput(),
            'occupation':forms.Select(choices= OCCUPATION)
        }


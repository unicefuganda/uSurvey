from django import forms
from survey.models import *
from django.forms import ModelForm
from django.core.validators import *
from survey.investigator_configs import TIME_MEASURE

class HouseholdHeadForm(ModelForm):

    class Meta:
        model = HouseholdHead
        exclude = ['household']
        widgets = {
            'surname': forms.TextInput(attrs={'placeholder': 'Name'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'male': forms.RadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'age': forms.TextInput(attrs={'placeholder': 'Age', 'min':13, 'type':'number' }),
            'occupation': forms.TextInput(attrs={'placeholder': 'Occupation'}),
            'time_measure': forms.RadioSelect(choices=TIME_MEASURE),
        }


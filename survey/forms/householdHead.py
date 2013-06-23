from django import forms
from survey.models import *
from django.forms import ModelForm
from django.core.validators import *

class HouseholdHeadForm(ModelForm):

    class Meta:
        model = HouseholdHead
        exclude = ['resident_since']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'male': forms.RadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'age': forms.TextInput(attrs={'placeholder': 'Age', 'min':13, 'type':'number' }),
            'occupation': forms.TextInput(attrs={'placeholder': 'Occupation'}),
        }


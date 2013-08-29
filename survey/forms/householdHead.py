from django import forms
from survey.models_file import *
from django.forms import ModelForm
from django.core.validators import *
from survey.investigator_configs import OCCUPATION, MONTHS
from widgets import InlineRadioSelect
from datetime import *

class HouseholdHeadForm(ModelForm):

    @staticmethod
    def resident_since_month_choices(choices):
        months = []
        for month in MONTHS:
            months.append({'value':month[0], 'text': month[1]})
        choices['choices']=months
        return choices

    @staticmethod
    def resident_since_year_choices(choices):
        year_now = datetime.now().year
        years = list(xrange(year_now-60, year_now+1, 1))
        years.reverse()
        choices['choices']= years
        return choices

    class Meta:
        model = HouseholdHead
        exclude = ['household']
        widgets = {
            'surname': forms.TextInput(attrs={'placeholder': 'Family Name'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Other Names'}),
            'male': InlineRadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'age': forms.TextInput(attrs={'placeholder': 'Age', 'min':10, 'max':99 }),
            'resident_since_year': forms.HiddenInput(),
            'resident_since_month': forms.HiddenInput(),
            'occupation': forms.Select(choices= OCCUPATION),
        }


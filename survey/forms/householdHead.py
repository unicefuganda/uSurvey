from django import forms
from survey.models import *
from django.forms import ModelForm
from django.core.validators import *
from survey.investigator_configs import OCCUPATION, MONTHS
from widgets import InlineRadioSelect
from datetime import *

class HouseholdHeadForm(ModelForm):

    @staticmethod
    def resident_since_month_choices():
        months = []
        for month in MONTHS:
            months.append({'value':month[0], 'text': month[1]})
        return months

    @staticmethod
    def resident_since_year_choices():
        year_now = datetime.now().year
        return xrange(year_now-60, year_now+1, 1)

    class Meta:
        model = HouseholdHead
        exclude = ['household']
        widgets = {
            'surname': forms.TextInput(attrs={'placeholder': 'Name'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'male': InlineRadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'age': forms.TextInput(attrs={'placeholder': 'Age', 'min':10, 'max':99, 'type':'number' }),
            'resident_since_year': forms.HiddenInput(),
            'resident_since_month': forms.HiddenInput(),
            'occupation': forms.Select(choices= OCCUPATION),
        }


from datetime import datetime
from django import forms
from django.forms import ModelForm, DateInput
from survey.models.households import HouseholdHead
from survey.interviewer_configs import OCCUPATION, MONTHS
from widgets import InlineRadioSelect


class HouseholdHeadForm(ModelForm):

    class Meta:
        model = HouseholdHead
        fields = ['surname', 'first_name',  'date_of_birth', 'gender',
                  'level_of_education', 'resident_since', 'occupation']

        widgets = {
            'surname': forms.TextInput(attrs={'placeholder': 'Family Name'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Other Names'}),
            'male': InlineRadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'occupation': forms.Select(choices= OCCUPATION),
        }

    date_of_birth = forms.DateField(label="Date of birth", widget=DateInput(attrs={'class':'datepicker'}), required=True, input_formats=["%Y-%m-%d"])
    resident_since = forms.DateField(widget=DateInput(attrs={'class':'datepicker'}), required=True, input_formats=["%Y-%m-%d"])


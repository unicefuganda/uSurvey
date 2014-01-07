from datetime import datetime
from django import forms
from django.forms import ModelForm, DateInput
from survey.models.households import HouseholdHead

from survey.investigator_configs import OCCUPATION, MONTHS
from widgets import InlineRadioSelect


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
        years = list(xrange(year_now - 60, year_now + 1, 1))
        years.reverse()
        choices['choices'] = years
        return choices

    class Meta:
        model = HouseholdHead
        fields = ['surname', 'first_name',  'date_of_birth', 'male', 'resident_since_year',
                  'level_of_education', 'resident_since_month', 'occupation']

        widgets = {
            'surname': forms.TextInput(attrs={'placeholder': 'Family Name'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Other Names'}),
            'male': InlineRadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'resident_since_year': forms.HiddenInput(),
            'resident_since_month': forms.HiddenInput(),
            'occupation': forms.Select(choices= OCCUPATION),
        }

    date_of_birth = forms.DateField(label="Date of birth", widget=DateInput(attrs={'class':'datepicker'}), required=True, input_formats=["%Y-%m-%d"])


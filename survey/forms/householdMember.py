import datetime
from django.forms import ModelForm, DateInput
from django import forms
from survey.models import HouseholdMember


class HouseholdMemberForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(HouseholdMemberForm, self).__init__(*args, **kwargs)

    class Meta:
        model = HouseholdMember
        fields = ['name', 'date_of_birth', 'male']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'male': forms.RadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            }

    date_of_birth = forms.DateField(label="Date of birth", widget=DateInput(attrs={'class':'datepicker'}), required=True, input_formats=["%Y-%m-%d"])


from django.forms import ModelForm, DateInput
from django import forms
from survey.models.households import HouseholdMember
from django.conf import settings


class HouseholdMemberForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(HouseholdMemberForm, self).__init__(*args, **kwargs)

    class Meta:
        model = HouseholdMember
        fields = ['surname', 'first_name', 'date_of_birth', 'gender']
        widgets = {
            'surname': forms.TextInput(attrs={'placeholder': 'Family Name'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Other Names'}),
            'male': forms.RadioSelect(choices=((True, 'Male'), (False, 'Female'))),
        }
    date_of_birth = forms.DateField(label="Date of birth", required=True, input_formats=[settings.DATE_FORMAT, ],
                                    widget=forms.DateInput(attrs={'placeholder': 'Date Of Birth',
                                                                  'class': 'datepicker'}, format=settings.DATE_FORMAT))

from django import forms
from survey.models import *
from django.forms import ModelForm

class HouseholdForm(ModelForm):

    class Meta:
        model = Household
        exclude = ['investigator']

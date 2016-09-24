from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models import Batch, Survey
from django.utils.safestring import mark_safe
from survey.models.formula import *


class InterviewerReportForm(forms.Form):
    survey = forms.ModelChoiceField(
        queryset=Survey.objects.all(), empty_label='----')
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.none(), empty_label='----', required=False)

    def __init__(self, *args, **kwargs):
        super(InterviewerReportForm, self).__init__(*args, **kwargs)
        if self.data.get('survey'):
            survey = Survey.objects.get(id=self.data['survey'])
            self.fields['batch'].queryset = survey.batches.all()

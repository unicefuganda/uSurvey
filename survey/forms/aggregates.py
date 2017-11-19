from django import forms
from survey.models import Batch, Survey


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

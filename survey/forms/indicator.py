from django import forms
from django.forms import ModelForm
from survey.models import Indicator, Batch, QuestionModule, Survey


class IndicatorForm(ModelForm):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), empty_label=None)

    def __init__(self, *args, **kwargs):
        super(IndicatorForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            survey = kwargs['instance'].survey
            self.fields['batch'].choices.queryset = survey.batches
        self.fields['module'].choices.queryset = QuestionModule.objects.all()
        self.fields['name'].label = 'Indicator'

    def clean(self):
        super(IndicatorForm, self).clean()
        batch = self.cleaned_data.get('batch', None)
        survey = self.cleaned_data.get('survey', None)

        if batch.survey != survey:
            message = "Batch %s does not belong to the selected Survey."% (batch.name)
            self._errors['batch'] = self.error_class([message])
            del self.cleaned_data['batch']
        return self.cleaned_data

    class Meta:
        model = Indicator
        fields = ['survey', 'batch', 'module', 'name', 'description', 'measure']
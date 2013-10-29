from django import forms
from django.forms import ModelForm
from survey.models import Indicator, Batch, QuestionModule, Survey


class IndicatorForm(ModelForm):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), empty_label=None)

    def __init__(self, *args, **kwargs):
        super(IndicatorForm, self).__init__(*args, **kwargs)
        self.fields['batch'].choices = map(lambda batch: (batch.id, batch.name), Batch.objects.all())
        self.fields['module'].choices = map(lambda module: (module.id, module.name), QuestionModule.objects.all())
        self.fields['name'].label = 'Indicator'
        self.fields.keyOrder=['survey', 'batch', 'module', 'name', 'description', 'measure']

    def clean(self):
        super(IndicatorForm, self).clean()
        batch = self.cleaned_data.get('batch', None)
        survey = self.cleaned_data.get('survey', None)

        if batch.survey != survey:
            message = "Batch %s is does not belong to the selected Survey."% (batch.name)
            self._errors['batch'] = self.error_class([message])
            del self.cleaned_data['batch']
        return self.cleaned_data

    class Meta:
        model = Indicator

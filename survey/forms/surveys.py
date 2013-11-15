from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from survey.forms.widgets import InlineRadioSelect
from survey.models.surveys import Survey


class SurveyForm(ModelForm):
    class Meta:
        model = Survey
        fields = ['name', 'description', 'type', 'has_sampling', 'sample_size']
        widgets = {
            'description': forms.Textarea(attrs={"rows": 4, "cols": 50}),
            'type': InlineRadioSelect(choices=((True, 'Aggregate'), (False, 'Roster'))),
        }

    has_sampling = forms.BooleanField(label="Enable Sampling", required=False, initial=True)


    def clean(self):
        cleaned_data = self.cleaned_data

        has_sampling = cleaned_data.get('has_sampling', None)

        if has_sampling and not cleaned_data.get('sample_size', None):
            raise ValidationError('Sample size must be specified if has sampling is selected.')

        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data['name']
        survey = Survey.objects.filter(name=name)
        instance_id = self.instance.id

        if not instance_id and survey:
            raise ValidationError("Survey with name %s already exist." % name)
        elif instance_id and survey and survey[0].id != instance_id:
            raise ValidationError("Survey with name %s already exist." % name)

        return self.cleaned_data['name']
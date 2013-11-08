from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from survey.models.surveys import Survey


class SurveyForm(ModelForm):
    class Meta:
        model = Survey
        fields = ['name', 'description', 'type', 'has_sampling', 'sample_size']
        widgets = {
            'type': forms.RadioSelect(choices=[(True, 'Aggregate'), ( False, 'Roster')]),
            'description': forms.Textarea(attrs={"rows": 4, "cols": 50})
        }

    def clean(self):
        cleaned_data = self.cleaned_data

        has_sampling = cleaned_data.get('has_sampling', None)

        if has_sampling and not cleaned_data.get('sample_size', None):
            raise ValidationError('Sample size must be specified if has sampling is selected.')

        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data['name']
        if Survey.objects.filter(name=name):
            raise ValidationError("Survey with name %s already exist." % name)
        return self.cleaned_data['name']
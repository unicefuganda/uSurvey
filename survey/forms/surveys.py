from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from survey.models.surveys import Survey


class SurveyForm(ModelForm):
    class Meta:
        model = Survey
        fields = ['name', 'description', 'type', 'sample_size']
        widgets = {
            'type': forms.RadioSelect(choices=[(True, 'Aggregate'), ( False, 'Roster')]),
            'description': forms.Textarea(attrs={"rows": 4, "cols": 50})
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if Survey.objects.filter(name=name):
            raise ValidationError("Survey with name %s already exist." % name)
        return self.cleaned_data['name']
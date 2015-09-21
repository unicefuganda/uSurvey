from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from survey.forms.widgets import InlineRadioSelect
from survey.models import Survey, BatchCommencement, SurveyHouseholdListing


class SurveyForm(ModelForm):
    # survey_listing = forms.CharField(choices=[(survey.pk, survey.name) for survey in Survey.objects.all()],
    #                                  help_text='Select survey household listing to reuse. Leave empty for fresh listing',
    #                                  required=False)
    class Meta:
        model = Survey
        fields = ['name', 'description', 'has_sampling', 'sample_size', 'preferred_listing']
        widgets = {
            'description': forms.Textarea(attrs={"rows": 4, "cols": 50}),
            'has_sampling': InlineRadioSelect(choices=((True, 'Sampled'), (False, 'Census')), attrs={'class' : 'has_sampling'}),
        }

    def __init__(self, *args, **kwargs):
        super(SurveyForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance', None) and kwargs['instance'].batches_enabled():
            del self.fields['preferred_listing']
        else:
            preferred_listings = [('', '------ None, Create new -------'), ]
            survey_listings = SurveyHouseholdListing.objects.all()
            preferred_listings.extend([(l.survey.pk, l.survey.name) for l in survey_listings])
            self.fields['preferred_listing'].choices = preferred_listings


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



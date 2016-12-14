from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from survey.models import RandomizationCriterion, CriterionTestArgument, QuestionOption, ListingTemplate
from survey.models import Answer, NumericalAnswer, TextAnswer, MultiChoiceAnswer, Interview
from survey.forms.widgets import InlineRadioSelect
from survey.forms.form_order_mixin import FormOrderMixin
from survey.models import Survey, BatchCommencement, SurveyHouseholdListing, AnswerAccessDefinition, USSDAccess


class SurveyForm(ModelForm):
    # survey_listing = forms.CharField(choices=[(survey.pk, survey.name) for survey in Survey.objects.all()],
    #                                  help_text='Select survey household listing to reuse. Leave empty for fresh listing',
    #                                  required=False)

    class Meta:
        model = Survey
        fields = ['name', 'description', 'has_sampling',
                  'sample_size', 'preferred_listing', 'listing_form']
        widgets = {
            'description': forms.Textarea(attrs={"rows": 4, "cols": 50}),
            'has_sampling': InlineRadioSelect(choices=((True, 'Sampled'), (False, 'Census')),
                                              attrs={'class': 'has_sampling'}),
        }

    def __init__(self, *args, **kwargs):
        super(SurveyForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance', None) and kwargs['instance'].has_sampling is False:
            self.fields['preferred_listing'].widget.attrs[
                'disabled'] = 'disabled'
        else:
            preferred_listings = [('', '------ None, Create new -------'), ]
            try:
                listing_forms = ListingTemplate.objects.values_list('pk', flat=True).order_by('id')
                survey_listings = Interview.objects.filter(pk__in=listing_forms).only('qset',
                                                                               'survey').distinct('qset', 'survey')
                preferred_listings.extend(
                    set([(l.survey.pk, l.survey.name) for l in survey_listings]))
                self.fields['preferred_listing'].choices = preferred_listings
            except Exception, err:
                print Exception, err
            

    def clean(self):
        cleaned_data = self.cleaned_data

        has_sampling = cleaned_data.get('has_sampling', None)

        if has_sampling and not cleaned_data.get('sample_size', None):
            raise ValidationError(
                'Sample size must be specified if has sampling is selected.')

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


class SamplingCriterionForm(forms.ModelForm, FormOrderMixin):
    min = forms.IntegerField(required=False)
    max = forms.IntegerField(required=False)
    value = forms.CharField(required=False)
    options = forms.ChoiceField(choices=[], required=False)

    def __init__(self, survey, *args, **kwargs):
        super(SamplingCriterionForm, self).__init__(*args, **kwargs)
        self.fields['survey'].initial = survey.pk
        self.fields['survey'].widget = forms.HiddenInput()
        self.fields['listing_question'].queryset = survey.listing_form.questions.filter(answer_type__in=[
            defin.answer_type for defin in AnswerAccessDefinition.objects.filter(channel=USSDAccess.choice_name())])
        self.order_fields(['listing_question', 'validation_test', 'options', 'value', 'min', 'max', 'survey'])
        if self.data.get('listing_question', []):
            options = QuestionOption.objects.filter(question__pk=self.data['listing_question'])
            self.fields['options'].choices = [(opt.text, opt.text) for opt in options]

    class Meta:
        exclude = []
        model = RandomizationCriterion
    #
    # def validate_options(self):
    #     listing_question = self.cleaned_data['listing_question']
    #
    #     return self.cleaned_data['options']

    def clean(self):
        validation_test = self.cleaned_data['validation_test']
        listing_question = self.cleaned_data['listing_question']
        answer_class = Answer.get_class(listing_question.answer_type)
        method = getattr(answer_class, validation_test, None)
        if method is None:
            raise ValidationError('unsupported validator defined on listing question')
        if validation_test == 'between':
            if self.cleaned_data.get('min', False) is False or self.cleaned_data.get('max', False) is False:
                raise ValidationError('min and max values required for between condition')
        elif self.cleaned_data.get('value', False) is False:
            raise ValidationError('Value is required for %s' % validation_test)
        if listing_question.answer_type == MultiChoiceAnswer.choice_name():
            if self.cleaned_data.get('options', False) is False:
                raise ValidationError('No option selected for %s' % listing_question.identifier)
            self.cleaned_data['value'] = self.cleaned_data['options']
        return self.cleaned_data

    def save(self, *args, **kwargs):
        criterion = super(SamplingCriterionForm, self).save(*args, **kwargs)
        if criterion.validation_test == 'between':
            criterion.arguments.create(position=0, param=self.cleaned_data['min'])
            criterion.arguments.create(position=1, param=self.cleaned_data['max'])
        else:
            criterion.arguments.create(position=0, param=self.cleaned_data['value'])
        return criterion



from django import forms
from django.forms import ModelForm
from survey.models import Interviewer, ODKAccess, USSDAccess, BatchLocationStatus, Survey, EnumerationArea, SurveyAllocation
from django.forms.models import inlineformset_factory
from django.conf import settings
from django.core.exceptions import ValidationError
import phonenumbers


class InterviewerForm(ModelForm):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), required=False)
    date_of_birth = forms.DateField(label="Date of birth", required=True, input_formats=[settings.DATE_FORMAT,],
                                    widget=forms.DateInput(attrs={'placeholder': 'Date Of Birth',
                                                                  'class': 'datepicker'}, format=settings.DATE_FORMAT))

    def __init__(self, eas, data=None, *args, **kwargs):
        super(InterviewerForm, self).__init__(data=data, *args, **kwargs)
        self.fields.keyOrder=['name', 'gender', 'date_of_birth', 'level_of_education', 'language',  'ea', 'survey']
        if self.instance:
            try:
                self.fields['survey'].initial = SurveyAllocation.objects.filter(interviewer=self.instance,
                                                                    status__in=[SurveyAllocation.PENDING,
                                                                            SurveyAllocation.COMPLETED])[0].survey.pk
            except IndexError:
                pass
        self.fields['ea'].queryset = eas

    class Meta:
        model = Interviewer
        fields = ['name',  'date_of_birth', 'gender', 'level_of_education', 'language',  'ea']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'gender': forms.RadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'ea': forms.Select(attrs={'class' : 'chzn-select ea_filter'}),
        }

    def clean_survey(self):
        ea = self.data.get('ea', '')
        if not ea:
            raise ValidationError('No Enumeration Area selected')
        survey = self.cleaned_data['survey']
        if survey:
            #check if this has already been allocated to someone else
            allocs = SurveyAllocation.objects.filter(survey=survey, status__in=[SurveyAllocation.PENDING,
                                                                                SurveyAllocation.COMPLETED],
                                               interviewer__ea=ea,
                                               allocation_ea=ea)
            if self.instance and self.instance.pk:
                allocs = allocs.exclude(interviewer=self.instance)
            if allocs.exists():
                raise ValidationError('Survey already active in %s for Interviewer %s' % (ea, allocs[0].interviewer))
        return survey


    # def clean(self):
    #     ea_id = self.data.get('ea')
    #     #check if interviewer is already active with survey in current EA
    #     if self.instance and self.instance.pk and ea_id != self.instance.ea.pk and self.instance.has_survey():
    #         raise ValidationError('Interviewer is having an active survey')
    #     return self.cleaned_data

    def save(self, commit=True, **kwargs):
        interviewer = super(InterviewerForm, self).save(commit=commit, **kwargs)
        if commit:
            survey = self.cleaned_data['survey']
            if survey:
                ea = self.cleaned_data['ea']
                interviewer.assignments.update(status=SurveyAllocation.DEALLOCATED)
                SurveyAllocation.objects.create(survey=survey,
                                                   interviewer=interviewer,
                                                   allocation_ea=ea)
        return interviewer


class USSDAccessForm(ModelForm):
    user_identifier = forms.CharField(label='Mobile Number',
                                      max_length=settings.MOBILE_NUM_MAX_LENGTH,
                                      min_length=settings.MOBILE_NUM_MIN_LENGTH,
                                      widget=forms.TextInput(attrs={'placeholder': 'Format: 771234567',
                                                                   'style':"width:172px;" ,
                                                                   'maxlength':settings.MOBILE_NUM_MAX_LENGTH,
                                                                    'minlength' : settings.MOBILE_NUM_MIN_LENGTH}))

    def __init__(self, *args, **kwargs):
        super(USSDAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['is_active', 'user_identifier',  ]

    class Meta:
        model = USSDAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer', 'aggregator']

    def clean_user_identifier(self):
        identifier = self.cleaned_data.get('user_identifier', '')
        try:
            identifier = phonenumbers.parse(identifier, settings.COUNTRY_CODE)
            if phonenumbers.is_valid_number_for_region(identifier, settings.COUNTRY_CODE):
                self.cleaned_data['user_identifier'] = identifier.national_number
            else:
                raise ValidationError('Invalid mobile number for your region')
        except phonenumbers.NumberParseException:
            raise ValidationError('Invalid mobile number')
        accesses = USSDAccess.objects.filter(user_identifier=identifier.national_number)
        if self.instance and accesses.exclude(interviewer=self.instance.interviewer).exists():
            raise ValidationError('This mobile number is already in use by %s' % accesses[0].interviewer.name)
        return self.cleaned_data['user_identifier']

class ODKAccessForm(ModelForm):
    user_identifier = forms.CharField(label='ODK ID')

    def __init__(self, *args, **kwargs):
        super(ODKAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['is_active', 'user_identifier', 'odk_token', ]


    def clean_user_identifier(self):
        identifier = self.cleaned_data.get('user_identifier', '')
        accesses = ODKAccess.objects.filter(user_identifier=identifier)
        if self.instance:
            try:
                accesses = accesses.exclude(interviewer=self.instance.interviewer)
            except Interviewer.DoesNotExist:
                pass
        if accesses.exists():
            raise ValidationError('This ODK ID is already in use by %s' % accesses[0].interviewer.name)
        return self.cleaned_data['user_identifier']

    class Meta:
        model = ODKAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer']


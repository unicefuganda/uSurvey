from django import forms
from django.forms import ModelForm
from survey.models import Interviewer, ODKAccess, USSDAccess, BatchLocationStatus, Survey, EnumerationArea, SurveyAllocation
from django.forms.models import inlineformset_factory
from django.conf import settings
from django.core.exceptions import ValidationError


class InterviewerForm(ModelForm):
    survey = forms.ChoiceField()
    date_of_birth = forms.DateField(label="Date of birth", required=True, input_formats=[settings.DATE_FORMAT,],
                                    widget=forms.DateInput(attrs={'placeholder': 'Date Of Birth',
                                                                  'class': 'datepicker'}, format=settings.DATE_FORMAT))

    def __init__(self, eas, data=None, *args, **kwargs):
        super(InterviewerForm, self).__init__(data=data, *args, **kwargs)
        self.fields.keyOrder=['name', 'gender', 'date_of_birth', 'level_of_education', 'language',  'ea', 'survey']
        survey_choices = [('', 'Select Survey')]
        if data and data.get('ea'):
            ea = EnumerationArea.objects.get(pk=data['ea'])
            open_surveys = ea.open_surveys()
            survey_choices.extend([(survey.pk, survey.name) for survey in open_surveys])
        else:
            extras = dict([(b.batch.survey.pk, b.batch.survey.name) for b in BatchLocationStatus.objects.all()]).items()
            survey_choices.extend(extras)
        self.fields['survey'].choices = survey_choices
        if self.instance:
            try:
                self.fields['survey'].initial = SurveyAllocation.objects.filter(interviewer=self.instance, completed=False)[0].survey.pk
            except IndexError:
                pass
        if eas:
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
        ea = self.cleaned_data.get('ea', '')
        survey_pk = self.cleaned_data['survey']
        if survey_pk.strip():
            if str(survey_pk.strip()) not in [str(s.pk) for s in ea.open_surveys()]:
                raise ValidationError('Survey does not belong to that Enumeration Area')
            survey = Survey.objects.get(pk=survey_pk)
            #check if this has already been allocated to someone else
            allocs = SurveyAllocation.objects.filter(survey=survey, completed=False,
                                               interviewer__ea=ea,
                                               allocation_ea=ea)
            if self.instance:
                allocs = allocs.exclude(interviewer=self.instance)
            if allocs.exists():
                raise ValidationError('Survey already active in %s for Interviewer %s' % (ea, allocs[0].interviewer))
            return survey


    def clean(self):
        ea = self.cleaned_data.get('ea')
        #check if interviewer is already active with survey in current EA
        if self.instance and self.instance.pk and ea.pk != self.instance.ea.pk and self.instance.has_survey():
            raise ValidationError('Interviewer is having an active survey')
        return self.cleaned_data

    def save(self, commit=True, **kwargs):
        interviewer = super(InterviewerForm, self).save(commit=commit, **kwargs)
        if commit:
            survey = self.cleaned_data['survey']
            ea = self.cleaned_data['ea']
            SurveyAllocation.objects.get_or_create(survey=survey,
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
        if identifier.isdigit() == False:
            raise ValidationError('Mobile number must contain only numbers')
        accesses = USSDAccess.objects.filter(user_identifier=identifier)
        if self.instance:
            try:
                accesses = accesses.exclude(interviewer=self.instance.interviewer)
            except Interviewer.DoesNotExist:
                pass
        if accesses.exists():
            raise ValidationError('This id mobile number is already in use by %s' % accesses[0].interviewer.name)
        return self.cleaned_data['user_identifier']
        


class ODKAccessForm(ModelForm):
    user_identifier = forms.CharField(label='ODK ID')

    def __init__(self, *args, **kwargs):
        super(ODKAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['is_active', 'user_identifier', 'odk_token', ]


    class Meta:
        model = ODKAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer']


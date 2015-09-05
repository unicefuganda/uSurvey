from django import forms
from django.forms import ModelForm
from survey.models import Interviewer, ODKAccess, USSDAccess, BatchLocationStatus, Survey
from django.forms.models import inlineformset_factory
from django.conf import settings
from django.core.exceptions import ValidationError


class InterviewerForm(ModelForm):
    date_of_birth = forms.DateField(label="Date of birth", required=True, input_formats=[settings.DATE_FORMAT,],
                                    widget=forms.DateInput(attrs={'placeholder': 'Date Of Birth',
                                                                  'class': 'datepicker'}, format=settings.DATE_FORMAT))

    def __init__(self, eas, data=None, *args, **kwargs):
        super(InterviewerForm, self).__init__(data=data, *args, **kwargs)
        self.fields.keyOrder=['name', 'gender', 'date_of_birth', 'level_of_education', 'language',  'ea']
        # most_principal_locs =
        # choices = dict([(b.batch.survey.pk, b.batch.survey.name) for b in BatchLocationStatus.objects.all()]).items()
        # choices.insert(0, ('', ' --- Select Survey ---'))
        # self.fields['survey'] = forms.ChoiceField()
        # self.fields['survey'].choices = choices
        # self.fields['survey'].required = False
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
            if survey_pk.strip() not in [s.pk for s in ea.open_surveys()]:
                raise ValidationError('Survey does not belong to that Enumeration Area')
            return Survey.objects.get(pk=survey_pk)

    def clean(self):
        ea = self.cleaned_data.get('ea')
        #check if interviewer is already active with survey in current EA
        if self.instance and self.instance.pk and ea.pk != self.instance.ea.pk and self.instance.has_survey():
            raise ValidationError('Interviewer is having an active survey')
        return self.cleaned_data


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
        return self.cleaned_data['user_identifier']
        


class ODKAccessForm(ModelForm):
    user_identifier = forms.CharField(label='ODK ID')

    def __init__(self, *args, **kwargs):
        super(ODKAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['is_active', 'user_identifier', 'odk_token', ]


    class Meta:
        model = ODKAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer']


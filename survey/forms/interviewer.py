from django import forms
from django.forms import ModelForm
from survey.models import Interviewer, ODKAccess, USSDAccess, BatchLocationStatus
from django.forms.models import inlineformset_factory
from django.conf import settings
from django.core.exceptions import ValidationError


class InterviewerForm(ModelForm):

    # survey = forms.ChoiceField(choices=)

    def __init__(self, ea_q_set=None, *args, **kwargs):
        super(InterviewerForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['name', 'gender', 'date_of_birth', 'level_of_education', 'language',  'ea']
        choices = dict([(b.batch.survey.pk, b.batch.survey.name) for b in BatchLocationStatus.objects.all()]).items()
        choices.insert(0, ('', ' --- Select Survey ---'))
        self.fields['survey'] = forms.ChoiceField()
        self.fields['survey'].choices = choices
        if ea_q_set:
           self.fields['ea'].queryset = ea_q_set

    class Meta:
        model = Interviewer
        fields = ['name',  'date_of_birth', 'gender', 'level_of_education', 'language',  'ea']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'gender': forms.RadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'date_of_birth': forms.TextInput(attrs={'placeholder': 'Date Of Birth', 'min':18, 'max':50 , 'class': 'datepicker'}),
            'ea': forms.Select(attrs={'class' : 'chzn-select ea_filter'}),
        }

    def clean_ea(self):
        ea = self.cleaned_data['ea']
        #check if interviewer is already active with survey in current EA
        if self.instance is not None and ea.pk != self.instance.ea.pk and self.instance.has_survey():
            raise ValidationError('Interviewer is having an active survey')

    def clean_survey(self):
        ea = self.cleaned_data['ea']
        survey = self.cleaned_data['survey']
        if survey.name.strip() not in [s.name for s in ea.open_surveys()]:
            raise ValidationError('Survey does not belong to that Enumeration Area')



class USSDAccessForm(ModelForm):
    user_identifier = forms.CharField(label='Mobile Number')

    def __init__(self, *args, **kwargs):
        super(USSDAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['is_active', 'user_identifier',  ]
    
    class Meta:
        model = USSDAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer', 'aggregator']
        


class ODKAccessForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(ODKAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['is_active', 'user_identifier', 'odk_token', ]


    class Meta:
        model = ODKAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer']


from django import forms
from django.forms import ModelForm
from survey.models import Interviewer, ODKAccess, USSDAccess
from django.forms.models import inlineformset_factory



class InterviewerForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(InterviewerForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['name', 'gender', 'date_of_birth', 'level_of_education', 'language',  'ea']

    class Meta:
        model = Interviewer
        fields = ['name',  'date_of_birth', 'gender', 'level_of_education', 'language',  'ea']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'gender': forms.RadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'date_of_birth': forms.TextInput(attrs={'placeholder': 'Date Of Birth', 'min':18, 'max':50 , 'class': 'datepicker'}),
            'ea': forms.Select(attrs={'class' : 'chzn-select'}),
        }
    

class USSDAccessForm(ModelForm):
    user_identifier = forms.CharField(label='Mobile Number')
    # is_active = forms.ChoiceField(label='', widget=forms.CheckboxInput)

    def __init__(self, *args, **kwargs):
        super(USSDAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['is_active', 'user_identifier',  ]
    
    class Meta:
        model = USSDAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer', 'aggregator']
        


class ODKAccessForm(ModelForm):
    is_active = forms.ChoiceField(label='', widget=forms.CheckboxInput)

    def __init__(self, *args, **kwargs):
        super(ODKAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['is_active', 'user_identifier', 'odk_token', ]


    class Meta:
        model = ODKAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer']


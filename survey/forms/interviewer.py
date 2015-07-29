from django import forms
from django.forms import ModelForm
from survey.models import Interviewer, ODKAccess, USSDAccess
from django.forms.models import inlineformset_factory



class InterviewerForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(InterviewerForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['name', 'gender', 'age', 'level_of_education', 'language',  'ea']

    class Meta:
        model = Interviewer
        fields = ['name',  'age', 'gender', 'level_of_education', 'language',  'ea']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'gender': forms.RadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'age': forms.TextInput(attrs={'placeholder': 'Age', 'min':18, 'max':50 }),
            'ea': forms.Select(attrs={'class' : 'chzn-select'}),
        }
    

class USSDAccessForm(ModelForm):
    user_identifier = forms.CharField(label='Mobile Number')
    
    class Meta:
        model = USSDAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer']
        


class ODKAccessForm(ModelForm):
    class Meta:
        model = ODKAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer']
        
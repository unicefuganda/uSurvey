from django import forms
from django.forms import ModelForm
from survey.models import Interviewer


class InterviewerForm(ModelForm):

    confirm_mobile_number = forms.CharField( widget=forms.TextInput(attrs={'placeholder': 'Format: 771234567', 'class':'no-paste',
                                                                            'style':"width:172px;" , 'maxlength':'10'}))
    def __init__(self, *args, **kwargs):
        super(InterviewerForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder=['name', 'male', 'age', 'level_of_education', 'language', 'backend', 'ea']
        self.fields['backend'].empty_label = None

    def clean(self):
        cleaned_data = super(InterviewerForm, self).clean()
        mobile_number = cleaned_data.get("mobile_number")
        confirm_mobile_number = cleaned_data.get("confirm_mobile_number")

        if mobile_number != confirm_mobile_number:
            message = "Mobile numbers don't match."
            self._errors["confirm_mobile_number"] = self.error_class([message])
            raise forms.ValidationError(message)

        return cleaned_data

    class Meta:
        model = Interviewer
        fields = ['name',  'age', 'level_of_education', 'language',  'ea']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'mobile_number': forms.TextInput(attrs={'placeholder': 'Format: 771234567', 'style':"width:172px;", 'maxlength':'10'}),
            'male': forms.RadioSelect(choices=((True, 'Male'), (False, 'Female'))),
            'age': forms.TextInput(attrs={'placeholder': 'Age', 'min':18, 'max':50 }),
            'location': forms.HiddenInput(),
            'ea': forms.HiddenInput(),
        }


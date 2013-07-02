from django import forms
from survey.models import *
from django.forms import ModelForm
from widgets import InlineRadioSelect

class WomenForm(ModelForm):
    has_women = forms.TypedChoiceField( initial=True, coerce=lambda x: x == 'True',
    widget=InlineRadioSelect, choices=((True, 'Yes'), (False, 'No')) )

    def __init__(self, *args, **kwargs):
        super(WomenForm, self).__init__(*args, **kwargs)
        self.fields['has_women'].label = 'Does this household have any women aged 15+ years?'
        self.fields.keyOrder= ['has_women', 'aged_between_15_19_years', 'aged_between_20_49_years']
        for key in ['has_women', 'aged_between_15_19_years', 'aged_between_20_49_years']:
            self.fields[key].required = False

    def check_has_women(self, cleaned_data):
        has_women = cleaned_data.get("has_women")
        if not has_women:
            for field in [ 'aged_between_15_19_years', 'aged_between_20_49_years']:
                field_value = cleaned_data.get(field)
                if not field_value and field_value !=0:
                    return cleaned_data
                if int(field_value):
                    self._errors[field] = self.error_class(["Should be zero. This household has no women aged 15+ years."])
                    del cleaned_data[field]
        return cleaned_data

    def clean(self):
        cleaned_data = super(WomenForm, self).clean()
        cleaned_data = self.check_has_women(cleaned_data)
        return cleaned_data

    class Meta:
        model = Women
        exclude = ['household']
        widgets ={
        'aged_between_15_19_years':forms.TextInput(attrs={'class':"small-positive-number", 'max':10, 'type':'number' }),
        'aged_between_20_49_years':forms.TextInput(attrs={'class':"small-positive-number", 'type':'number' }),
        }


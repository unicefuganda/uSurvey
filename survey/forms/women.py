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
        self.fields.keyOrder= ['has_women', 'aged_between_15_19_years', 'aged_between_15_49_years']

    def check_has_women(self, cleaned_data):
        has_women = cleaned_data.get("has_women")
        if not has_women:
            for field in [ 'aged_between_15_19_years', 'aged_between_15_49_years']:
                if int(cleaned_data.get(field)):
                    self._errors[field] = self.error_class(["Should be zero. This household has no women aged 15+ years."])
                    del cleaned_data[field]
        return cleaned_data

    def check_aged_15_49(self, cleaned_data):
        aged_between_15_49_years = cleaned_data.get('aged_between_15_49_years')
        if not aged_between_15_49_years and aged_between_15_49_years !=0:
            return cleaned_data

        aged_between_15_19_years = cleaned_data.get('aged_between_15_19_years')
        if not aged_between_15_19_years:
            return cleaned_data

        if int(aged_between_15_19_years) > int(aged_between_15_49_years):
            self._errors["aged_between_15_49_years"] = self.error_class(["Should be higher than the number of women between 15 to 19 years age."])
            del cleaned_data['aged_between_15_49_years']
        return cleaned_data

    def clean(self):
        cleaned_data = super(WomenForm, self).clean()
        cleaned_data = self.check_has_women(cleaned_data)
        cleaned_data = self.check_aged_15_49(cleaned_data)
        return cleaned_data

    class Meta:
        model = Women
        exclude = ['household']
        widgets ={
        'aged_between_15_19_years':forms.TextInput(attrs={'min':0, 'type':'number' }),
        'aged_between_15_49_years':forms.TextInput(attrs={'min':0, 'type':'number' }),
        }


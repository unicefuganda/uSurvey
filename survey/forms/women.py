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

    def check_women_above_15_is_less_than_total_number_of_females_in_household(self, cleaned_data):
        aged_between_15_19_years = cleaned_data.get('aged_between_15_19_years') if cleaned_data.get('aged_between_15_19_years') else 0
        aged_between_20_49_years = cleaned_data.get('aged_between_20_49_years') if cleaned_data.get('aged_between_20_49_years') else 0
        total_women_above_15 = int(aged_between_15_19_years) + int(aged_between_20_49_years)

        household = self.instance.household
        number_of_females = household.number_of_females if household else None

        if number_of_females and number_of_females < total_women_above_15:
            for key in list(set(['aged_between_15_19_years', 'aged_between_20_49_years']) & set(cleaned_data.keys())):
                self._errors[key] = self.error_class(["The total number of women above 15 cannot be greater than the number of females in this household."])
                del cleaned_data[key]
        return cleaned_data


    def clean(self):
        cleaned_data = super(WomenForm, self).clean()
        cleaned_data = self.check_has_women(cleaned_data)
        cleaned_data = self.check_women_above_15_is_less_than_total_number_of_females_in_household(cleaned_data)
        return cleaned_data

    class Meta:
        model = Women
        exclude = ['household']
        widgets ={
        'aged_between_15_19_years':forms.TextInput(attrs={'class':"small-positive-number", 'type':'number' }),
        'aged_between_20_49_years':forms.TextInput(attrs={'class':"small-positive-number", 'type':'number' }),
        }


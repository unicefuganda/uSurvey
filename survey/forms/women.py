from django import forms
from survey.models import *
from django.forms import ModelForm

class WomenForm(ModelForm):
    has_women = forms.BooleanField( widget=forms.RadioSelect(choices=((True, 'Yes'), (False, 'No'))), initial=False)

    def __init__(self, *args, **kwargs):
        super(WomenForm, self).__init__(*args, **kwargs)
        self.fields['has_women'].label = 'Does this household have any women aged 15+ years?'
        self.fields.keyOrder= ['has_women', 'aged_between_15_19_years', 'aged_between_15_49_years']


    def clean(self):
      cleaned_data = super(WomenForm, self).clean()
      has_women = cleaned_data.get("has_women")

      if not has_women:
        message = "Should be zero. This household has no women aged 15+ years."
        for field in [ 'aged_between_15_19_years', 'aged_between_15_49_years']:
            if int(cleaned_data.get(field)):
                self._errors[field] = self.error_class([message])
                del cleaned_data[field]

      return cleaned_data

    class Meta:
        model = Women
        exclude = ['household']

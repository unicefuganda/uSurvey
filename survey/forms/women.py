from django import forms
from survey.models import *
from django.forms import ModelForm

class WomenForm(ModelForm):
    has_women = forms.BooleanField( widget=forms.RadioSelect(choices=((True, 'Yes'), (False, 'No'))))

    def __init__(self, *args, **kwargs):
        super(WomenForm, self).__init__(*args, **kwargs)
        self.fields['has_women'].label = 'Does this household have any women aged 15+ years?'
        self.fields.keyOrder= ['has_women', 'aged_between_15_19_years', 'aged_between_15_49_years']


    def clean(self):
      cleaned_data = super(WomenForm, self).clean()
      has_children = cleaned_data.get("has_children")

      if not has_children:
        message = "Should be zero. This household has no women aged 15+ years."
        for field in [ 'aged_between_15_19_years', 'aged_between_15_49_years']:
            if int(cleaned_data.get(field)):
                self._errors[field] = self.error_class([message])
                raise forms.ValidationError(message)

      return cleaned_data

    class Meta:
        model = Women
        exclude = ['household']

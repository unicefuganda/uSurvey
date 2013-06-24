from django import forms
from survey.models import *
from django.forms import ModelForm

class ChildrenForm(ModelForm):
    has_children = forms.BooleanField( widget=forms.RadioSelect(choices=((True, 'Yes'), (False, 'No'))))

    def clean(self):
      cleaned_data = super(InvestigatorForm, self).clean()
      has_children = cleaned_data.get("has_children")

      if not has_children:
        message = "Should be zero. This household has no children."
        for field in [ 'aged_between_5_12_years', 'aged_between_13_17_years', 'aged_between_0_5_months',
                       'aged_between_6_11_months', 'aged_between_12_23_months', 'aged_between_24_59_months']:
            if int(cleaned_data.get(field)):
                self._errors[field] = self.error_class([message])
                raise forms.ValidationError(message)

      return cleaned_data

    class Meta:
        model = Children
        exclude = ['household']

from django import forms
from survey.models import *
from django.forms import ModelForm
from django.core.validators import *

class HouseHoldForm(ModelForm):

    size = forms.CharField( widget=forms.TextInput(attrs={'type':'number'}))

    def clean(self):
      cleaned_data = super(InvestigatorForm, self).clean()
      mobile_number = cleaned_data.get("mobile_number")
      confirm_mobile_number = cleaned_data.get("confirm_mobile_number")

      if mobile_number != confirm_mobile_number:
        message = "Mobile numbers don't match."
        self._errors["confirm_mobile_number"] = self.error_class([message])
        raise forms.ValidationError(message)

      return cleaned_data

    class Meta:
        model = HouseHold
        exclude = ['head', 'investigator']

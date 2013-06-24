from django import forms
from survey.models import *
from django.forms import ModelForm

class HouseHoldForm(ModelForm):

    size = forms.CharField( widget=forms.TextInput(attrs={'type':'number'}))

    def clean(self):
      cleaned_data = super(InvestigatorForm, self).clean()
      number_of_males = cleaned_data.get("number_of_males")
      number_of_females = cleaned_data.get("number_of_females")
      size = cleaned_data.get("size")

      if int(size) != int(number_of_females) + int(number_of_males):
        message = "Total number of household members doesn't match female and male ones."
        self._errors["size"] = self.error_class([message])
        raise forms.ValidationError(message)

      return cleaned_data

    class Meta:
        model = HouseHold
        exclude = ['investigator']

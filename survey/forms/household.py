from django import forms
from survey.models import *
from django.forms import ModelForm

class HouseholdForm(ModelForm):

    size = forms.CharField( widget=forms.TextInput(attrs={'type':'number', 'value':0}))

    def __init__(self, *args, **kwargs):
            super(HouseholdForm, self).__init__(*args, **kwargs)
            self.fields['size'].label = 'Total number of persons in this household'

    def clean(self):
      cleaned_data = super(HouseholdForm, self).clean()
      number_of_males = cleaned_data.get("number_of_males")
      number_of_females = cleaned_data.get("number_of_females")
      size = cleaned_data.get("size")

      if int(size) != int(number_of_females) + int(number_of_males):
        message = "Total number of household members doesn't match female and male ones."
        self._errors["size"] = self.error_class([message])
        del cleaned_data['size']

      return cleaned_data

    class Meta:
        model = Household
        exclude = ['investigator']
        widgets = {
        'number_of_males':forms.TextInput(attrs={'min':0, 'type':'number' }),
        'number_of_females':forms.TextInput(attrs={'min':0, 'type':'number' }),
        }

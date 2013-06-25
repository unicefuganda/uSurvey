from django import forms
from survey.models import *
from django.forms import ModelForm

class ChildrenForm(ModelForm):
    has_children = forms.BooleanField( widget=forms.RadioSelect(choices=((True, 'Yes'), (False, 'No'))))
    has_children_below_5 = forms.BooleanField( widget=forms.RadioSelect(choices=((True, 'Yes'), (False, 'No'))))
    total_below_5 = forms.CharField( widget=forms.TextInput(attrs={'type':'number'}))

    def __init__(self, *args, **kwargs):
        super(ChildrenForm, self).__init__(*args, **kwargs)
        self.fields['has_children'].label = 'Does this household have any children?'
        self.fields['has_children_below_5'].label = 'Does this household have any children aged below 5 years?'
        self.fields['total_below_5'].label = 'Total number of children aged below 5 years'
        self.fields.keyOrder= ['has_children', 'aged_between_5_12_years', 'aged_between_13_17_years', 'has_children_below_5',
                    'aged_between_0_5_months',  'aged_between_6_11_months', 'aged_between_12_23_months',
                     'aged_between_24_59_months', 'total_below_5']

    def clean_attribute(self, has_children, message, against_attributes, cleaned_data):
        if not has_children:
          message = "Should be zero. This household has no children" + message
          for field in against_attributes:
              if int(cleaned_data.get(field)):
                  self._errors[field] = self.error_class([message])
                  del cleaned_data[field]
        return cleaned_data

    def check_total_below_5(self, cleaned_data, fields_for_below_5):
        total_below_5 = cleaned_data.get("total_below_5")
        message = "Total does not match."
        total = 0
        for field in fields_for_below_5:
            total += int(cleaned_data.get(field))
        if total != total_below_5:
            self._errors[field] = self.error_class([message])
            del cleaned_data["total_below_5"]
        return cleaned_data

    def clean(self):
        cleaned_data = super(ChildrenForm, self).clean()
        below_5 = cleaned_data.get("has_children_below_5")
        for_below_5 = [ 'aged_between_0_5_months', 'aged_between_6_11_months', 'aged_between_12_23_months', 'aged_between_24_59_months']
        cleaned_data = self.clean_attribute(below_5, " below 5 years.", for_below_5, cleaned_data)

        has_children = cleaned_data.get("has_children")
        for_has_children = [ 'aged_between_5_12_years', 'aged_between_13_17_years'] + for_below_5
        cleaned_data = self.clean_attribute(has_children, ".", for_has_children, cleaned_data)

        cleaned_data = self.check_total_below_5(cleaned_data, for_below_5)

        return cleaned_data

    class Meta:
        model = Children
        exclude = ['household']

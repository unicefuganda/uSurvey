from django import forms
from django.forms import ModelForm
from survey.models.location_type_details import LocationTypeDetails


class LocationDetailsForm(ModelForm):
    levels = forms.CharField(label= 'Level1', max_length=50, required=True)

    class Meta:
        model = LocationTypeDetails
        fields = ['required', 'has_code', 'length_of_code']

        widgets = {
            'has_code': forms.CheckboxInput(attrs={'class':'has_code'}),
        }
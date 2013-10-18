from django import forms
from django.forms import ModelForm
from survey.models.location_type_details import LocationTypeDetails


class LocationDetailsForm(ModelForm):
    levels = forms.CharField(label= 'Level1', max_length=50, required=True)
    class Meta:
        model = LocationTypeDetails
        fields = ['required', 'has_code', 'code',]

        required = forms.BooleanField(required=False,initial=False,label='required')
        has_code = forms.BooleanField(required=False,initial=False,label='has code')
        code = forms.CharField(label= 'Code', max_length=30, required=False)

    def clean(self):
        has_code = self.cleaned_data.get('has_code')
        code = self.cleaned_data.get('code')
        if has_code:
            if code == '':
                message = "Code cannot be blank if has code is checked."
                self._errors["code"] = self.error_class([message])
                raise forms.ValidationError(message)

        return self.cleaned_data
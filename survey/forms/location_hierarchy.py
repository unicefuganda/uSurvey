from django import forms
from rapidsms.contrib.locations.models import Location


class LocationHierarchyForm(forms.Form):
    def __init__(self,data=None):
        super(LocationHierarchyForm, self).__init__(data=data)
        self.COUNTRY_CHOICES = [(country.id,country.name) for country in Location.objects.filter(type__name__iexact='country')]

        self.fields['country'] = forms.ChoiceField(label='Country', choices=self.COUNTRY_CHOICES, widget=forms.Select, required=True)
        self.fields['levels'] = forms.CharField(label= 'Level1', max_length=50, required=True)
        self.fields['required'] = forms.BooleanField(required=False,initial=False,label='required')
        self.fields['has_code'] = forms.BooleanField(required=False,initial=False,label='has code')
        self.fields['code'] = forms.CharField(label= 'Code', max_length=30, required=False)

    def clean(self):
        cleaned_data = super(LocationHierarchyForm, self).clean()
        has_code = cleaned_data.get("has_code")
        code = cleaned_data.get("code")

        if has_code:
            if not code:
                message = "Code cannot be blank if has code is checked."
                self._errors["code"] = self.error_class([message])
                raise forms.ValidationError(message)

        return cleaned_data


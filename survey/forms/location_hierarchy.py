from django import forms
from django.forms.formsets import BaseFormSet
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import LocationTypeDetails


class BaseArticleFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        for form_count in range(0, self.total_form_count()):
            form = self.forms[form_count]
            has_code = form.cleaned_data.get('has_code',None)
            code = form.cleaned_data.get('code','')
            if has_code:
                if not code:
                    message = "Code cannot be blank if has code is checked."
                    form._errors["code"] = form.error_class([message])
                    raise forms.ValidationError(message)

class LocationHierarchyForm(forms.Form):
    def __init__(self,data=None):
        super(LocationHierarchyForm, self).__init__(data=data)
        self.fields['country'] = forms.ChoiceField(label='Country', choices=self.get_country_choices(), widget=forms.Select, required=True)

    def get_country_choices(self):
        existing_country_details = LocationTypeDetails.objects.exclude(country=None)
        if existing_country_details:
            existing_country = existing_country_details[0].country
            return [(existing_country.id, existing_country.name)]
        return [(country.id,country.name) for country in Location.objects.filter(type__name__iexact='country')]


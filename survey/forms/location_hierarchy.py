from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from rapidsms.contrib.locations.models import Location
from survey.forms.location_details import LocationDetailsForm
from survey.models import LocationTypeDetails


class BaseArticleFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
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
        existing_country_details = LocationTypeDetails.objects.filter(location_type__name__iexact='country').exclude(country=None)
        if existing_country_details:
            existing_country = existing_country_details[0].country
            return [(existing_country.id, existing_country.name)]
        return [(country.id,country.name) for country in Location.objects.filter(type__name__iexact='country')]


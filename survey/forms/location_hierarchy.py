from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from rapidsms.contrib.locations.models import Location
from survey.forms.location_details import LocationDetailsForm



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
        self.COUNTRY_CHOICES = [(country.id,country.name) for country in Location.objects.filter(type__name__iexact='country')]
        self.fields['country'] = forms.ChoiceField(label='Country', choices=self.COUNTRY_CHOICES, widget=forms.Select, required=True)

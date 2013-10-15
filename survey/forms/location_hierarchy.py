from django import forms
from rapidsms.contrib.locations.models import Location


class LocationHierarchyForm(forms.Form):
    COUNTRY_CHOICES = [(country.id,country.name) for country in Location.objects.filter(type__name='country')]
    country = forms.ChoiceField(label='Country', choices=COUNTRY_CHOICES, widget=forms.Select, required=True)
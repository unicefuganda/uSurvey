from django import forms
from rapidsms.contrib.locations.models import Location


class LocationHierarchyForm(forms.Form):
    def __init__(self):
        super(LocationHierarchyForm, self).__init__()
        self.COUNTRY_CHOICES = [(country.id,country.name) for country in Location.objects.filter(type__name__iexact='country')]

        self.fields['country'] = forms.ChoiceField(label='Country', choices=self.COUNTRY_CHOICES, widget=forms.Select, required=True)
        self.fields['levels'] = forms.CharField(label= 'Level1', max_length=50, required=False)
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.conf import settings
from survey.models import EnumerationArea, Location, LocationType


class EnumerationAreaForm(ModelForm):

#     locations = forms.ModelMultipleChoiceField(queryset=Location.objects.all(),
#                                                widget=forms.SelectMultiple(attrs={'class': 'multi-select enumeration_area', 'id': 'ea-locations'}))
    
    def __init__(self, *args, **kwargs):
        super(EnumerationAreaForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['name', 'total_households']
        location_type = LocationType.objects.all()[0].get_leafnodes()[0] #I'll allow this to fail if no Location type has been defined
        self.fields['locations'].queryset = Location.objects.filter(type=location_type)
        self.fields.keyOrder.append('locations')

    class Meta:
        model = EnumerationArea

        widgets = {
            'name': forms.TextInput(attrs={"id": 'ea_name', "class": 'enumeration_area'}),
            'total_households' : forms.TextInput({'id' : 'total_households',  "class": 'enumeration_area'}),
            'locations': forms.SelectMultiple(attrs={'class': 'multi-select enumeration_area', 'id': 'ea-locations'})
        }

class EnumerationAreaFilterForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(EnumerationAreaForm, self).__init__(*args, **kwargs)
        for location_type in LocationType.objects.all():
            if location_type.is_leaf_node() == false:
                choices = [(loc.pk, loc.name) for loc in Location.objects.filter(type=location_type)]
                choices.insert(0, ('', '--------------------------------'))
                self.fields[location_type.name] = forms.ChoiceField(choices=choices)  

    class Meta:
        model = EnumerationArea
    
    def filter(self, locations):
        query_dict = None
        if self.is_valid():
            for key in self.fields.keys():
                query_dict['key'] = self.cleaned_data[key]
            for key, val in query_dict.items():
                if val == 'All' or not val:
                    del query_dict[key]
        if query_dict is None:
            for key in self.fields.keys():
                query_dict['%s__in'%key] = [key for key, val in  self.fields[key].choices if not val == '']
        return locations.filter(**query_dict)

# 
#     def save(self, commit=True, **kwargs):
#         batch = super(EnumerationAreaForm, self).save(commit=commit)
#         bc = BatchChannel.objects.filter(batch=batch)
#         bc.delete()
#         for val in kwargs['access_channels']:
#            BatchChannel.objects.create(batch=batch, channel=val)

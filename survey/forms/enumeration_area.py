from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Form
from django.conf import settings
from survey.models import EnumerationArea, Location, LocationType

class EnumerationAreaForm(ModelForm):
    
    def __init__(self, locations=None, *args, **kwargs):
        super(EnumerationAreaForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['name', ]
        locations = locations or LocationsFilterForm().get_locations()
        self.fields['locations'].queryset = locations
        self.fields.keyOrder.append('locations')

    class Meta:
        model = EnumerationArea
        widgets = {
            'name': forms.TextInput(attrs={"id": 'ea_name', "class": 'enumeration_area'}),
            'total_households' : forms.TextInput({'id' : 'total_households',  "class": 'enumeration_area'}),
            'locations': forms.SelectMultiple(attrs={'class': 'multi-select enumeration_area', 'id': 'ea-locations'})
        }

class LocationsFilterForm(Form):
    '''
        1. Used to filter out locations under a given main location (eg states under a country)
        2. Also to filter out locations under given ea if defined
    '''
    
    def __init__(self, *args, **kwargs):
        include_ea = kwargs.pop('include_ea', False)
        super(LocationsFilterForm, self).__init__(*args, **kwargs)
        data = kwargs.get('data', {})
        for location_type in LocationType.objects.all():
            if location_type.parent is not None and location_type.is_leaf_node() == False:
                kw = {'type':location_type}
                parent_selection = data.get(location_type.parent.name, None)
                if parent_selection:
                    kw['parent__pk'] = parent_selection
                locations = Location.objects.filter(**kw)
                # choices = [(loc.pk, loc.name) for loc in locations]
                # choices.insert(0, ('', '--- Select %s ---' % location_type.name))
                self.fields[location_type.name] = forms.ModelChoiceField(queryset=locations) #forms.ChoiceField(choices=choices)
                self.fields[location_type.name].required = False
                self.fields[location_type.name].widget.attrs['class'] = 'location_filter ea_filter chzn-select'
                # self.fields[location_type.name].widget.attrs['style'] = 'width: 100px;'
        if include_ea:
            eas = EnumerationArea.objects.filter(locations__in=locations).order_by('name')
            choices = [(ea.pk, ea.name) for ea in eas]
            choices.insert(0, ('', '--- Select EA ---'))
            self.fields['enumeration_area'] = forms.ChoiceField(choices=choices)
            self.fields['enumeration_area'].widget.attrs['class'] = 'location_filter chzn-select'
            # self.fields['enumeration_area'].widget.attrs['style'] = 'width: 100px;'
            self.fields['enumeration_area'].required = False

    
    def get_locations(self):
        loc = None
        ea = None
        if self.is_valid():
            for key in self.fields.keys():
                if key is not 'enumeration_area':
                    val = self.cleaned_data[key]
                    if val: 
                        loc = val
                else:
                    ea = self.cleaned_data[key] or None
        return get_leaf_locs(loc, ea)

    def get_enumerations(self):
        return EnumerationArea.objects.filter(locations__in=self.get_locations()).distinct().order_by('name')
    
def get_leaf_locs(loc=None, ea=None):
    if loc is None:
        location = Location.objects.get(parent=None)
    else:
        location = loc
    locations = location.get_leafnodes(True)
    if ea:
        locations = locations.filter(enumeration_areas__pk__in=ea)
    return locations.distinct()

# 
#     def save(self, commit=True, **kwargs):
#         batch = super(EnumerationAreaForm, self).save(commit=commit)
#         bc = BatchChannel.objects.filter(batch=batch)
#         bc.delete()
#         for val in kwargs['access_channels']:
#            BatchChannel.objects.create(batch=batch, channel=val)

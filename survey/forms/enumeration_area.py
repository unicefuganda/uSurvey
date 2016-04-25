from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Form
from django.conf import settings
from survey.models import EnumerationArea, Location, LocationType
from django.http import QueryDict

class EnumerationAreaForm(ModelForm):
    
    def __init__(self, locations=None, *args, **kwargs):
        super(EnumerationAreaForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['name', ]
        locations = locations or LocationsFilterForm().get_locations()
        self.fields['locations'].queryset = locations
        self.fields.keyOrder.append('locations')

    class Meta:
        model = EnumerationArea
        exclude = []
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

    last_location_selected = None

    def __init__(self, *args, **kwargs):
        include_ea = kwargs.pop('include_ea', False)
        super(LocationsFilterForm, self).__init__(*args, **kwargs)
        data = self.data
        if not isinstance(self.data, QueryDict):
            self.data = QueryDict('', mutable=True)
            self.data.update(data)
        self.data._mutable = True
        last_selected_pk = None
        largest_unit = LocationType.largest_unit()
        locations = Location.objects.none()
        for location_type in LocationType.objects.all():
            if location_type.parent is not None and location_type.is_leaf_node() == False:
                kw = {'type':location_type}
                parent_selection = data.get(location_type.parent.name, None)
                if (locations and parent_selection) or location_type == largest_unit:
                    if parent_selection:
                        last_selected_pk = data.get(location_type.name, None) or parent_selection
                        kw['parent__pk'] = parent_selection
                    locations = Location.objects.filter(**kw)
                else:
                    self.data[location_type.name] = ''
                    locations = Location.objects.none()
                # choices = [(loc.pk, loc.name) for loc in locations]
                # choices.insert(0, ('', '--- Select %s ---' % location_type.name))
                self.fields[location_type.name] = forms.ModelChoiceField(queryset=locations) #forms.ChoiceField(choices=choices)
                self.fields[location_type.name].required = False
                self.fields[location_type.name].widget.attrs['class'] = 'location_filter ea_filters chzn-select'
                # self.fields[location_type.name].widget.attrs['style'] = 'width: 100px;'
        if last_selected_pk:
            self.last_location_selected = Location.objects.get(pk=last_selected_pk)
        if include_ea:
            if self.last_location_selected:
                eas = EnumerationArea.objects.filter(locations__in=get_leaf_locs(loc=self.last_location_selected)).distinct()
            else:
                eas = EnumerationArea.objects.none()
            choices = [(ea.pk, ea.name) for ea in eas]
            choices.insert(0, ('', '--- Select EA ---'))
            self.fields['enumeration_area'] = forms.ModelChoiceField(queryset=eas)#ChoiceField(choices=choices)
            self.fields['enumeration_area'].widget.attrs['class'] = 'location_filter chzn-select'
            # self.fields['enumeration_area'].widget.attrs['style'] = 'width: 100px;'
            self.fields['enumeration_area'].required = False
        self.data._mutable = False

    
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
                    ea = self.cleaned_data.get(key, None)
        return get_leaf_locs(loc, ea)

    def get_enumerations(self):
        return EnumerationArea.objects.filter(locations__in=self.get_locations()).distinct().order_by('name')
    
def get_leaf_locs(loc=None, ea=None):
    if Location.objects.exists():
        if not loc:
            location = Location.objects.get(parent=None)
        else:
            if isinstance(loc, Location):
                location = loc
            else:
                location = Location.objects.get(pk=loc)
        locations = location.get_leafnodes(True)
        if ea:
            locations = locations.filter(enumeration_areas=ea)
        return locations.distinct()
    else:
        return Location.objects.none()

# 
#     def save(self, commit=True, **kwargs):
#         batch = super(EnumerationAreaForm, self).save(commit=commit)
#         bc = BatchChannel.objects.filter(batch=batch)
#         bc.delete()
#         for val in kwargs['access_channels']:
#            BatchChannel.objects.create(batch=batch, channel=val)

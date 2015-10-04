from django.utils.datastructures import SortedDict
from survey.models import LocationTypeDetails, EnumerationArea, Location, LocationType


class LocationWidget(object):
    EA_WIDGET_KEY = 'Enumeration area'

    def __init__(self, selected_location, ea=None, level=None):
        super(LocationWidget, self).__init__()
        self.selected_location = selected_location
        self.selected_locations = []
        self.level = level
        self.selected_ea = ea

    def get_widget_data(self):
        if not self.selected_location:
            return self.get_parent()
        else:
            return self.get_data_for_selected_location(self.selected_location)

    def sorted_by_hierarchy(self, old_data):
        data = SortedDict()
        location_types_excluding_country_and_village = self.get_all_location_types()
        for ltype in location_types_excluding_country_and_village:
            data[ltype.slug] = old_data[ltype.slug] if old_data.has_key(ltype.slug) else []
        return data

    def get_all_location_types(self):
        types = LocationType.objects.exclude(name__iexact='country').exclude(pk=LocationType.smallest_unit().pk)
        if not self.level:
            return list(types)
        return types.filter(level__lte=self.level)[1:]

    def has_location_selected(self, location):
        return location in self.selected_locations

    def get_data_for_selected_location(self, location):
        data = {}
        self.selected_locations.append(location)
        self.get_ancestors_data(data, location)
        self.get_siblings_data(data, location)
        self.get_children_data(data, location)
        return self.sorted_by_hierarchy(data)

    def get_siblings_data(self, data, location):
        data[location.type.slug] = location.get_siblings(include_self=True).order_by('name')

    def get_ancestors_data(self, data, location):
        location = location.parent
        if location.parent is None:
            return
        self.selected_locations.append(location)
        self.get_siblings_data(data, location)
        self.get_ancestors_data(data, location)

    def get_children_data(self, data, location):
        location = location.get_children()
        if location:
            self.get_siblings_data(data, location[0])

    def get_parent(self):
        largest_loc_type = LocationType.largest_unit()
        locations = Location.objects.filter(type=largest_loc_type).order_by('name')
        return {largest_loc_type.slug: locations } #self.sorted_by_hierarchy({largest_loc_type.slug: locations }) if locations else {}

    def next_type_in_hierarchy(self):
        children = self.selected_location.get_children()
        if children:
            return children[0].type

    def get_ea_data(self):
        if self.level or not self.selected_location:
            return
        if self.selected_type_is_second_lowest():
            return EnumerationArea.under_(self.selected_location)
        if self.selected_ea:
            return self.selected_ea.get_siblings()

    def selected_type_is_second_lowest(self):
        return self.selected_location.type == LocationType.smallest_unit().parent.type
               #LocationTypeDetails.get_second_lowest_level_type()
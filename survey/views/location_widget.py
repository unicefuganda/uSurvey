from rapidsms.contrib.locations.models import Location, LocationType
from django.utils.datastructures import SortedDict
from survey.models import LocationTypeDetails


class LocationWidget(object):

    def __init__(self, selected_location, level=None):
        super(LocationWidget, self).__init__()
        self.selected_location = selected_location
        self.selected_locations = []
        self.level = level

    def get_widget_data(self):
        if not self.selected_location:
            return self.get_tree_parent()
        else:
            return self.get_data_for_selected_location(self.selected_location)

    def sorted_by_hierarchy(self, old_data):
        data = SortedDict()
        all_types = self.get_all_location_types()
        location_types_excluding_country = all_types.values_list('location_type', flat=True)[1:]
        for slug in location_types_excluding_country:
            data[slug] = old_data[slug] if old_data.has_key(slug) else []
        return data

    def get_all_location_types(self):
        all_types = LocationTypeDetails.objects.order_by('order')
        if self.level:
            all_types = all_types.filter(order__lte=self.level)
        return all_types

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
        location = location.tree_parent
        if location.tree_parent is None:
            return
        self.selected_locations.append(location)
        self.get_siblings_data(data, location)
        self.get_ancestors_data(data, location)

    def get_children_data(self, data, location):
        location = location.get_children()
        if location:
            self.get_siblings_data(data, location[0])

    def get_tree_parent(self):
        the_country = LocationTypeDetails.the_country
        locations = Location.objects.filter(tree_parent=the_country).order_by('name')
        return self.sorted_by_hierarchy({locations[0].type.slug: locations }) if locations else {}

    def next_type_in_hierarchy(self):
        children = self.selected_location.get_children()
        if children:
            return children[0].type
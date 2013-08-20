from rapidsms.contrib.locations.models import Location, LocationType
from django.utils.datastructures import SortedDict

class LocationWidget(object):

    def __init__(self, selected_location):
        super(LocationWidget, self).__init__()
        self.selected_location = selected_location
        self.selected_locations = []

    def get_widget_data(self):
        if not self.selected_location:
            return self.get_tree_parent()
        else:
            return self.get_data_for_selected_location(self.selected_location)

    def sorted_by_hierarchy(self, old_data):
        data = SortedDict()
        for slug in LocationType.objects.values('slug'):
            slug = slug['slug']
            data[slug] = old_data[slug] if old_data.has_key(slug) else []
        return data

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
        if not location:
            return
        self.selected_locations.append(location)
        self.get_siblings_data(data, location)
        self.get_ancestors_data(data, location)

    def get_children_data(self, data, location):
        location = location.get_children()
        if location:
            self.get_siblings_data(data, location[0])

    def get_tree_parent(self):
        locations = Location.objects.filter(tree_parent=None).order_by('name')
        type_slug = locations[0].type.slug
        return self.sorted_by_hierarchy({ type_slug: locations })

    def next_type_in_hierarchy(self):
        children = self.selected_location.get_children()
        if children:
            return children[0].type
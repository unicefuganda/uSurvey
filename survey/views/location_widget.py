from rapidsms.contrib.locations.models import Location, LocationType

class LocationWidget(object):

    def __init__(self, selected_location):
        super(LocationWidget, self).__init__()
        self.selected_location = selected_location

    def get_widget_data(self):
        if not self.selected_location:
            return self.get_tree_parent()
        else:
            return self.get_data_for_selected_location(self.selected_location)

    def get_data_for_selected_location(self, location):
        data = {}
        self.get_siblings_data(data, location)
        self.get_ancestors_data(data, location)
        self.get_children_data(data, location)
        return data

    def get_siblings_data(self, data, location):
        data[location.type.slug] = location.get_siblings(include_self=True)

    def get_ancestors_data(self, data, location):
        location = location.tree_parent
        if not location:
            return
        self.get_siblings_data(data, location)
        self.get_ancestors_data(data, location)

    def get_children_data(self, data, location):
        location = location.get_children()
        if location:
            self.get_siblings_data(data, location[0])

    def get_tree_parent(self):
        locations = Location.objects.filter(tree_parent=None)
        type_slug = locations[0].type.slug
        return { type_slug: locations }
from django.utils.datastructures import SortedDict
from rapidsms.contrib.locations.models import *


def initialize_location_type(default_select):
    selected_location = SortedDict()
    all_type = LocationType.objects.all()
    for location_type in all_type:
        selected_location[location_type.name] = {'value': '', 'text': default_select, 'siblings': []}
    district = all_type[0]
    selected_location[district.name]['siblings'] = Location.objects.filter(tree_parent=None).order_by('name')
    return selected_location


def assign_ancestors_locations(selected_location, location):
    ancestors = location.get_ancestors(include_self=True)
    for loca in ancestors:
        selected_location[loca.type.name]['value'] = loca.id
        all_default_select = selected_location[loca.type.name]['text']
        selected_location[loca.type.name]['text'] = loca.name
        siblings = list(loca.get_siblings().order_by('name'))
        siblings.insert(0, {'id': '', 'name': all_default_select})
        selected_location[loca.type.name]['siblings'] = siblings
    return selected_location


def assign_immediate_child_locations(selected_location, location):
    children = location.get_descendants()
    if children:
        immediate_child = children[0]
        siblings = immediate_child.get_siblings(include_self=True).order_by('name')
        selected_location[immediate_child.type.name]['siblings'] = siblings
    return selected_location


def update_location_type(selected_location, location_id):
    if not location_id:
        return selected_location
    location = Location.objects.get(id=location_id)
    selected_location = assign_ancestors_locations(selected_location, location)
    selected_location = assign_immediate_child_locations(selected_location, location)
    return selected_location


def get_posted_location(location_data):
    location_id = ''
    for location_type in LocationType.objects.all():
        if location_data[location_type.name.lower()]:
            location_id = location_data[location_type.name.lower()]
    return location_id
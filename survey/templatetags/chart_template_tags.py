from django import template
from django.contrib import messages
import json
register = template.Library()

@register.filter
def title_for_barchart(formula, locations):
    title = "%s for %s" % (formula.name, title_for_location_type(locations))
    return title

@register.filter
def location_names(hierarchial_data):
    names = [str(location.name) for location in hierarchial_data.keys()]
    return names

@register.filter
def title_for_location_type(locations):
    next_type_in_hierarchy = locations.next_type_in_hierarchy()
    if next_type_in_hierarchy:
        return next_type_in_hierarchy.name

@register.filter
def get_values(hierarchial_data):
    return hierarchial_data.values()

@register.filter
def is_float(value):
    return type(value) == float
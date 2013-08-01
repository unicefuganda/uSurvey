from django import template
from django.contrib import messages

register = template.Library()

@register.filter
def is_location_selected(locations_data, location):
    if locations_data.has_location_selected(location):
        return "selected='selected'"

@register.filter
def is_batch_selected(batch, selected_batch):
    if batch == selected_batch:
        return "selected='selected'"

@register.filter
def pending_households(investigator, batch):
    return investigator.pending_households_for(batch)

@register.filter
def is_batch_open_for_location(open_locations, location):
    if location in open_locations:
        return "checked='checked'"

@register.filter
def is_mobile_number(field):
    return 'mobile number' in field.lower()

@register.filter
def is_radio(field):
    if "radio" in str(field):
        return "radio_field"
    return ""
from django import template

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

# @register.simple_tag

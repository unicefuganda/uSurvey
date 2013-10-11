from django import template
from survey.investigator_configs import MONTHS
from django.core.urlresolvers import reverse
from survey.models.helper_constants import CONDITIONS

register = template.Library()

@register.filter
def is_mobile_number(field):
  return 'mobile number' in field.lower()

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
    if "radio" in str(field) and not "select" in str(field):
        return "radio_field"
    return ""

@register.filter
def display_list(list):
    new_list = [str(item) for item in list]
    return ', '.join(new_list)

@register.filter
def get_value(dict, key):
    return dict.get(key, "")

@register.filter
def get_month(index):
    if not str(index).isdigit() and not index :
        return "N/A"
    return MONTHS[int(index)][1]

@register.filter
def format_date(date):
    return date.strftime("%b %d, %Y")

@register.filter
def get_url_with_ids(args, url_name):
    if not str(args).isdigit():
      arg_list = [int(arg) for arg in args.split(',')]
      return reverse(url_name, args=arg_list)
    return reverse(url_name, args=(args,))    

@register.filter
def get_url_without_ids(url_name):
    return reverse(url_name)    

@register.filter
def add_string(int_1, int_2):
    return "%s, %s"%(str(int_1), str(int_2))

@register.filter
def condition_text(key):
    value = CONDITIONS.get(key, "")
    return value

from django import template
from django.core.urlresolvers import reverse

from survey.investigator_configs import MONTHS
from survey.models.helper_constants import CONDITIONS
from survey.utils.views_helper import get_ancestors


register = template.Library()

@register.filter
def is_location_selected(locations_data, location):
    if locations_data.has_location_selected(location):
        return "selected='selected'"

@register.filter
def is_ea_selected(locations_data, ea):
    if locations_data.selected_ea == ea:
        return "selected='selected'"


@register.filter
def is_selected(batch, selected_batch):
    if batch == selected_batch:
        return "selected='selected'"

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

@register.filter
def modulo(num, val):
    return num % val == 0

@register.filter
def repeat_string(string, times):
    return string*(times-1)

@register.filter
def is_survey_selected_given(survey, selected_batch):
    if not selected_batch or not selected_batch.survey:
        return None

    if survey == selected_batch.survey:
        return "selected='selected'"

@register.filter
def non_response_is_activefor(open_locations, location):
    if location in open_locations:
       return "checked='checked'"

@register.filter
def ancestors_reversed(location):
    ancestors = get_ancestors(location)
    ancestors.reverse()
    return ancestors

@register.filter
def household_completed_percent(investigator):
#    import pdb;pdb.set_trace()
    households = investigator.households.all()
    total = households.count()
    completed = len([hld for hld in households.all() if hld.survey_completed() and hld.household_member.count() > 0])
    if total > 0:
        return "%s%%" % str(completed*100/total)

@register.filter
def has_open_allocated_surveys(investigator):
    return any([hld.survey_completed() for hld in investigator.households.all()])
    

@register.filter
def total_household_members(investigator):
    households = investigator.households.all()
    return sum([household.household_member.count() for household in households])


import json
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django import forms

from rapidsms.contrib.locations.models import *
from survey.forms.householdHead import *
from survey.forms.children import *
from survey.forms.women import *
from survey.forms.household import *
from survey.views.location_filter_helper import initialize_location_type, update_location_type
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist

CREATE_HOUSEHOLD_DEFAULT_SELECT = ''

def _get_posted_location(location_data):
    location_id = ''
    for location_type in LocationType.objects.all():
        if location_data[location_type.name.lower()]:
            location_id = location_data[location_type.name.lower()]
    return location_id


def _add_error_response_message(householdform, request):
    error_message = "Household not registered. "
    messages.error(request, error_message + "See errors below.")

    for key in householdform.keys():
        form = householdform[key]
        if form.non_field_errors():
            for err in form.non_field_errors():
                messages.error(request, error_message + str(err))

def validate_investigator(request, householdform, posted_locations):
    investigator_form = {'value':'', 'text':'', 'error':'',
                         'options': Investigator.objects.filter(location__in=posted_locations)}
    investigator = None
    try:
        investigator = Investigator.objects.get(id=int(request.POST['investigator']))
        investigator_form['text']= investigator.name
        investigator_form['value']= investigator.id
    except MultiValueDictKeyError:
        message = "No investigator provided."
        investigator_form['error']= message
        householdform.errors['__all__'] = householdform.error_class([message])
    except (ObjectDoesNotExist, ValueError):
        investigator_form['text']= request.POST['investigator']
        investigator_form['value']= request.POST['investigator']
        message = "You provided an unregistered investigator."
        investigator_form['error']= message
        householdform.errors['__all__'] = householdform.error_class([message])
    return investigator, investigator_form

def _process_form(householdform, investigator, request):
    valid ={}
    is_valid_household = householdform['household'].is_valid()
    if investigator and is_valid_household:
        householdform['household'].instance.investigator = investigator
        householdform['household'].save()
        valid['household'] = True
    remaining_keys = ['householdHead', 'children', 'women']
    for key in remaining_keys:
        is_valid_form = householdform[key].is_valid()
        if is_valid_household and is_valid_form:
            householdform[key].instance.household= householdform['household'].instance
            householdform[key].save()
            valid[key] = True
    if valid.values().count(True)==len(householdform.keys()):
        messages.success(request, "Household successfully registered.")
        return HttpResponseRedirect("/households/new")

    for key in valid.keys():
        householdform[key].instance.delete()
    _add_error_response_message(householdform, request)
    return None

def set_household_form(data):
    householdform={}
    householdform['householdHead'] = HouseholdHeadForm(data=data, auto_id='household-%s', label_suffix='')
    householdform['children'] = ChildrenForm(data=data,auto_id='household-children-%s', label_suffix='')
    householdform['women'] =  WomenForm(data=data,auto_id='household-women-%s', label_suffix='')
    householdform['household']= HouseholdForm(data=data, auto_id='household-%s', label_suffix='')
    return householdform

def new(request):
    location_type = initialize_location_type(default_select=CREATE_HOUSEHOLD_DEFAULT_SELECT)
    response = None
    householdform = set_household_form(data=None)
    investigator_form = {'value':'', 'text':'', 'options': Investigator.objects.all(), 'error':''}

    if request.method == 'POST':
        householdform = set_household_form(data=request.POST)
        location_id = _get_posted_location(request.POST)
        location_type = update_location_type(location_type, location_id)
        posted_locations = Location.objects.get(id=int(location_id)).get_descendants(include_self=True)
        investigator, investigator_form = validate_investigator(request, householdform['household'],  posted_locations)
        response = _process_form(householdform, investigator, request)

    householdHead = householdform['householdHead']
    del householdform['householdHead']
    return response or render(request, 'households/new.html', {  'location_type': location_type,
                                                                 'investigator_form': investigator_form,
                                                                  'headform': householdHead,
                                                                  'householdform': householdform,
                                                                  'action':"/households/new/",
                                                                  'id':"create-household-form",
                                                                  'button_label':"Create Household",
                                                                  'loading_text':"Creating..."})

def get_investigators(request):
  location = request.GET['location'] if request.GET.has_key('location') and request.GET['location'] else None
  investigators = Investigator.objects.filter(location=location)
  investigator_hash = {}
  for investigator in investigators:
      investigator_hash[investigator.name] = investigator.id
  return HttpResponse(json.dumps(investigator_hash), content_type="application/json")


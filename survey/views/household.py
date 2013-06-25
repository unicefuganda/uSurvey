from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages

from rapidsms.contrib.locations.models import *
from survey.forms.householdHead import *
from survey.forms.children import *
from survey.forms.women import *
from survey.forms.household import *
from survey.views.location_filter_helper import initialize_location_type, update_location_type

CREATE_HOUSEHOLD_DEFAULT_SELECT = ''

def _get_posted_location(location_data):
    location_id = ''
    for location_type in LocationType.objects.all():
        if location_data[location_type.name.lower()]:
            location_id = location_data[location_type.name.lower()]
    return location_id


def _add_error_response_message(form_list, request):
    form_list = [item for sublist in form_list for item in sublist]
    error_message = "Household not registered. "
    messages.error(request, error_message + "See errors below.")
    for form in form_list:
        if form.non_field_errors():
            for err in form.non_field_errors():
                messages.error(request, error_message + str(err))


def _process_form(household, dependent_forms, request):
    investigator = Investigator.objects.get(id=int(request.POST['investigator']))
    valid =[]
    if household.is_valid():
        household.investigator = investigator
        valid.append(True)
    for form in dependent_forms:
        if form.is_valid():
            form.household= household
            valid.append(True)
    if valid.count(True)==len(dependent_forms)+1:
        household.resident_since=3
        household.save()
        for form in dependent_forms:
            form.save()
        messages.success(request, "Household successfully registered.")
        return HttpResponseRedirect("/households/new")

    _add_error_response_message([household, dependent_forms], request)
    return None

def new(request):
    location_type = initialize_location_type(default_select=CREATE_HOUSEHOLD_DEFAULT_SELECT)
    response = None

    householdHead = HouseholdHeadForm(auto_id='household-%s', label_suffix='')
    children = ChildrenForm(auto_id='household-%s', label_suffix='')
    women =  WomenForm(auto_id='household-%s', label_suffix='')
    household= HouseHoldForm(auto_id='household-%s', label_suffix='')
    investigators = Investigator.objects.all()

    if request.method == 'POST':
        householdHead = HouseholdHeadForm(data=request.POST, auto_id='household-%s', label_suffix='')
        children = ChildrenForm(data=request.POST,auto_id='household-%s', label_suffix='')
        women =  WomenForm(data=request.POST,auto_id='household-%s', label_suffix='')
        household= HouseHoldForm(data=request.POST, auto_id='household-%s', label_suffix='')
        location_id = _get_posted_location(request.POST)
        location_type = update_location_type(location_type, location_id)
        response = _process_form(household, [householdHead, children, women], request)
        posted_locations = Location.objects.get(id=int(location_id)).get_descendants(include_self=True)
        investigators = Investigator.objects.filter(location__in=posted_locations)


    householdform =[household, children, women]

    return response or render(request, 'households/new.html', {  'location_type': location_type,
                                                                 'investigators': investigators,
                                                                  'headform': householdHead,
                                                                  'householdform': householdform,
                                                                  'action':"/households/new/",
                                                                  'id':"create-household-form",
                                                                  'button_label':"Create Household",
                                                                  'loading_text':"Creating..."})

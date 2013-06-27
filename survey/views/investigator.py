import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages

from survey.investigator_configs import *
from rapidsms.contrib.locations.models import Location, LocationType
from survey.forms.investigator import *
from survey.models import Investigator
from survey.views.views_helper import initialize_location_type, update_location_type, get_posted_location


CREATE_INVESTIGATOR_DEFAULT_SELECT = ''
LIST_INVESTIGATOR_DEFAULT_SELECT = 'All'


def _add_error_response_message(investigator, request):
    error_message = "Investigator not registered. "
    messages.error(request, error_message + "See errors below.")

    for field in investigator.hidden_fields():
        if field.errors:
            messages.error(request, error_message + field.label + " information required.")

    if investigator.non_field_errors():
        for err in investigator.non_field_errors():
            messages.error(request, error_message + str(err))


def _process_form(investigator, request):
    if investigator.is_valid():
        investigator.save()
        # Household.objects.create(investigator=investigator.instance)
        messages.success(request, "Investigator successfully registered.")
        return HttpResponseRedirect("/investigators/")

    _add_error_response_message(investigator, request)
    return None


def new_investigator(request):
    investigator = InvestigatorForm(auto_id='investigator-%s', label_suffix='')
    location_type = initialize_location_type(default_select=CREATE_INVESTIGATOR_DEFAULT_SELECT)
    response = None

    if request.method == 'POST':
        investigator = InvestigatorForm(data=request.POST, auto_id='investigator-%s', label_suffix='')
        location_id = get_posted_location(request.POST)
        location_type = update_location_type(location_type, location_id)
        response = _process_form(investigator, request)

    return response or render(request, 'investigators/new.html', {'country_phone_code': COUNTRY_PHONE_CODE,
                                                                  'location_type': location_type,
                                                                  'form': investigator,
                                                                  'action': "/investigators/new/",
                                                                  'id': "create-investigator-form",
                                                                  'button_label': "Create Investigator",
                                                                  'loading_text': "Creating..."})


def get_locations(request):
    tree_parent = request.GET['parent'] if request.GET.has_key('parent') and request.GET['parent'] else None
    locations = Location.objects.filter(tree_parent=tree_parent)
    location_hash = {}
    for location in locations:
        location_hash[location.name] = location.id
    return HttpResponse(json.dumps(location_hash), content_type="application/json")


def list_investigators(request):
    selected_location = initialize_location_type(default_select=LIST_INVESTIGATOR_DEFAULT_SELECT)
    investigators = Investigator.objects.all()

    return render(request, 'investigators/index.html',
                  {'investigators': investigators,
                   'location_type': selected_location,
                   'request': request})


def filter_list_investigators(request, location_id):
    the_location = Location.objects.get(id=int(location_id));
    corresponding_locations = the_location.get_descendants(include_self=True)
    investigators = Investigator.objects.filter(location__in=corresponding_locations)

    return_selected_location = update_location_type(
        initialize_location_type(default_select=LIST_INVESTIGATOR_DEFAULT_SELECT), location_id)

    return render(request, 'investigators/index.html',
                  {'investigators': investigators,
                   'location_type': return_selected_location,
                   'selected_location_type': the_location.type.name.lower(),
                   'request': request})


def check_mobile_number(request):
    response = Investigator.objects.filter(mobile_number=request.GET['mobile_number']).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

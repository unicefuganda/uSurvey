import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages

from survey.investigator_configs import *
from rapidsms.contrib.locations.models import Location, LocationType
from survey.forms.investigator import *
from survey.models import Investigator
from survey.views.views_helper import initialize_location_type, update_location_type, get_posted_location
from survey.views.location_widget import LocationWidget

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
    tree_parent = request.GET['parent'] if request.GET.has_key('parent') and request.GET['parent'].isdigit() else None
    locations = Location.objects.filter(tree_parent=tree_parent)
    location_hash = {}
    for location in locations:
        location_hash[location.name] = location.id
    return HttpResponse(json.dumps(location_hash), content_type="application/json")

def list_investigators(request):
    params = request.GET
    selected_location = None
    investigators = Investigator.objects.all()

    if params.has_key('location') and params['location'].isdigit():
        selected_location = Location.objects.get(id=int(params['location']));
        corresponding_locations = selected_location.get_descendants(include_self=True)
        investigators = Investigator.objects.filter(location__in=corresponding_locations)

    if not investigators:
        location_type = selected_location.type.name.lower() if selected_location and selected_location.type else 'location'
        messages.error(request, "There are  no investigators currently registered  for this %s." % location_type)

    return render(request, 'investigators/index.html',
                  {'investigators': investigators,
                   'location_data': LocationWidget(selected_location),
                   'request': request})


def check_mobile_number(request):
    response = Investigator.objects.filter(mobile_number=request.GET['mobile_number']).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

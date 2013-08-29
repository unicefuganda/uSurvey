import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages

from survey.investigator_configs import *
from rapidsms.contrib.locations.models import Location, LocationType
from survey.forms.investigator import *
from survey.models import Investigator
from survey.views.location_widget import LocationWidget
from django.contrib.auth.decorators import login_required, permission_required
from survey.views.views_helper import contains_key

CREATE_INVESTIGATOR_DEFAULT_SELECT = ''
LIST_INVESTIGATOR_DEFAULT_SELECT = 'All'

def _add_error_response_message(investigator, request,action_text):
    error_message = "Investigator not %s. " % action_text
    messages.error(request, error_message + "See errors below.")

    for field in investigator.hidden_fields():
        if field.errors:
            messages.error(request, error_message + field.label + " information required.")

    if investigator.non_field_errors():
        for err in investigator.non_field_errors():
            messages.error(request, error_message + str(err))

def _process_form(investigator, request, action_text,
                  redirect_url):
    if investigator.is_valid():
        investigator.save()
        # Household.objects.create(investigator=investigator.instance)
        messages.success(request, "Investigator successfully %s " % action_text)
        return HttpResponseRedirect(redirect_url)
    _add_error_response_message(investigator, request,action_text)
    return None

@login_required
@permission_required('auth.can_view_investigators')
def new_investigator(request):
    investigator = InvestigatorForm(label_suffix='')
    selected_location = None
    response = None

    if request.method == 'POST':
        investigator = InvestigatorForm(data=request.POST, label_suffix='')
        selected_location = Location.objects.get(id=request.POST['location']) if contains_key(request.POST, 'location') else None
        action_text = "registered."
        redirect_url = "/investigators/"
        response = _process_form(investigator, request, action_text, redirect_url)

    return response or render(request, 'investigators/investigator_form.html', {'country_phone_code': COUNTRY_PHONE_CODE,
                                                                  'locations': LocationWidget(selected_location),
                                                                  'form': investigator,
                                                                  'action': "/investigators/new/",
                                                                  'title': 'New Investigator',
                                                                  'id': "create-investigator-form",
                                                                  'class': 'investigator-form',
                                                                  'button_label': "Create Investigator",
                                                                  'loading_text': "Creating..."})
@login_required
def get_locations(request):
    tree_parent = request.GET['parent'] if request.GET.has_key('parent') and request.GET['parent'].isdigit() else None
    locations = Location.objects.filter(tree_parent=tree_parent)
    location_hash = {}
    for location in locations:
        location_hash[location.name] = location.id
    return HttpResponse(json.dumps(location_hash), content_type="application/json")

@login_required
@permission_required('auth.can_view_investigators')
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

@login_required
def check_mobile_number(request):
    response = Investigator.objects.filter(mobile_number=request.GET['mobile_number']).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

@permission_required('auth.can_view_investigators')
def show_investigator(request, investigator_id):
    investigator = Investigator.objects.get(id=investigator_id)
    return render(request, 'investigators/show.html', {'investigator': investigator})

@permission_required('auth.can_view_investigators')
def edit_investigator(request, investigator_id):
    response = None
    investigator = Investigator.objects.get(id=investigator_id)
    investigator_form = InvestigatorForm(instance=investigator, initial= {'confirm_mobile_number':investigator.mobile_number})
    if request.method == 'POST':
        investigator_form = InvestigatorForm(data=request.POST, instance=investigator)
        action_text = "edited."
        redirect_url = "/investigators/%s" % investigator_id
        response = _process_form(investigator_form, request, action_text, redirect_url)

    context = { 'action': '/investigators/' + str(investigator_id) + '/edit/',
                'country_phone_code': COUNTRY_PHONE_CODE,
                'title': 'Edit Investigator',
                'id': 'edit-investigator-form',
                'class': 'investigator-form',
                'button_label': 'Save',
                'loading_text': 'Saving...',
                'form': investigator_form,
                'locations': LocationWidget(investigator.location)}
    return response or render(request, 'investigators/investigator_form.html', context)
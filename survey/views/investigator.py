import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from rapidsms.contrib.locations.models import Location
from django.contrib.auth.decorators import login_required, permission_required

from survey.investigator_configs import *
from survey.forms.investigator import *
from survey.models import EnumerationArea
from survey.models.investigator import Investigator
from survey.views.location_widget import LocationWidget
from survey.utils.views_helper import contains_key

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


def _process_form(investigator_form, request, action_text,
                  redirect_url):
    if investigator_form.is_valid():
        investigator = investigator_form.save()
        investigator.remove_invalid_households()
        messages.success(request, "Investigator successfully %s " % action_text)
        return HttpResponseRedirect(redirect_url)
    _add_error_response_message(investigator_form, request,action_text)
    return None

@login_required
@permission_required('auth.can_view_investigators')
def new_investigator(request):
    investigator = InvestigatorForm(label_suffix='')
    selected_location = None
    selected_ea = None
    response = None

    if request.method == 'POST':
        investigator = InvestigatorForm(data=request.POST, label_suffix='')
        selected_location = Location.objects.get(id=request.POST['location']) if contains_key(request.POST, 'location') else None
        selected_ea = EnumerationArea.objects.get(id=request.POST['ea']) if contains_key(request.POST, 'ea') else None
        action_text = "registered."
        redirect_url = "/investigators/"
        response = _process_form(investigator, request, action_text, redirect_url)

    return response or render(request, 'investigators/investigator_form.html', {'country_phone_code': COUNTRY_PHONE_CODE,
                                                                  'locations': LocationWidget(selected_location, ea=selected_ea),
                                                                  'form': investigator,
                                                                  'action': "/investigators/new/",
                                                                  'title': 'New Investigator',
                                                                  'id': "create-investigator-form",
                                                                  'class': 'investigator-form',
                                                                  'button_label': "Create",
                                                                  'cancel_url': '/investigators/',
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
    selected_ea = None
    investigators = Investigator.objects.order_by('id')

    if params.has_key('location') and params['location'].isdigit():
        selected_location = Location.objects.get(id=int(params['location']))
        corresponding_locations = selected_location.get_descendants(include_self=True)
        investigators = investigators.filter(ea__locations__in=corresponding_locations)

    if params.has_key('ea') and params['ea'].isdigit():
        selected_ea = EnumerationArea.objects.get(id=int(params['ea']))
        investigators = investigators.filter(ea=selected_ea)

    if not investigators:
        location_type = selected_location.type.name.lower() if selected_location and selected_location.type else 'location'
        messages.error(request, "There are  no investigators currently registered  for this %s." % location_type)

    location_widget = LocationWidget(selected_location, ea=selected_ea)
    return render(request, 'investigators/index.html',
                  {'investigators': investigators,
                   'location_data': location_widget,
                   'request': request})


@login_required
@permission_required('survey.view_completed_survey')
def show_completion_summary(request, investigator_id):
    investigator = Investigator.objects.get(pk=investigator_id)
    return render(request, 'investigators/completion_summary.html', {'investigator': investigator})


@login_required
def check_mobile_number(request):
    response = Investigator.objects.filter(mobile_number=request.GET['mobile_number']).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

@permission_required('auth.can_view_investigators')
def show_investigator(request, investigator_id):
    investigator = Investigator.objects.get(id=investigator_id)
    return render(request, 'investigators/show.html', {'investigator': investigator, 'cancel_url': '/investigators/'})

@permission_required('auth.can_view_investigators')
def edit_investigator(request, investigator_id):
    response = None
    investigator = Investigator.objects.get(id=investigator_id)
    selected_location = investigator.location
    selected_ea = investigator.ea
    investigator_form = InvestigatorForm(instance=investigator, initial= {'confirm_mobile_number':investigator.mobile_number})
    if request.method == 'POST':
        investigator_form = InvestigatorForm(data=request.POST, instance=investigator)
        action_text = "edited."
        redirect_url = "/investigators/"
        selected_location = Location.objects.get(id=request.POST['location']) if contains_key(request.POST, 'location') else None
        selected_ea = EnumerationArea.objects.get(id=request.POST['ea']) if contains_key(request.POST, 'ea') else None
        response = _process_form(investigator_form, request, action_text, redirect_url)

    context = { 'action': '/investigators/%s/edit/' % investigator_id,
                'country_phone_code': COUNTRY_PHONE_CODE,
                'title': 'Edit Investigator',
                'id': 'edit-investigator-form',
                'class': 'investigator-form',
                'button_label': 'Save',
                'cancel_url': '/investigators/',
                'loading_text': 'Saving...',
                'form': investigator_form,
                'locations': LocationWidget(selected_location, ea=selected_ea)}
    return response or render(request, 'investigators/investigator_form.html', context)

@permission_required('auth.can_view_investigators')
def block_investigator(request, investigator_id):
    try:
        investigator = Investigator.objects.get(id=investigator_id)
        investigator.is_blocked = True
        investigator.save()
        investigator.households.clear()
        messages.success(request, "Investigator successfully blocked.")
    except Investigator.DoesNotExist:
        messages.error(request, "Investigator does not exist.")
    return HttpResponseRedirect('/investigators/')

@permission_required('auth.can_view_investigators')
def unblock_investigator(request, investigator_id):
    try:
        investigator = Investigator.objects.get(id=investigator_id)
        investigator.is_blocked = False
        investigator.save()
        messages.success(request, "Investigator successfully unblocked.")
    except Investigator.DoesNotExist:
        messages.error(request, "Investigator does not exist.")
    return HttpResponseRedirect('/investigators/')

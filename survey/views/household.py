import json

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, permission_required

from rapidsms.contrib.locations.models import *
from survey.forms.householdHead import *
from survey.forms.household import *
from survey.models.households import Household
from survey.models.investigator import Investigator
from survey.views.location_widget import LocationWidget
from survey.views.views_helper import contains_key


CREATE_HOUSEHOLD_DEFAULT_SELECT = ''


def _add_error_response_message(householdform, request):
    error_message = "Household not registered. "
    messages.error(request, error_message + "See errors below.")

    for key in householdform.keys():
        form = householdform[key]
        if form.non_field_errors():
            for err in form.non_field_errors():
                messages.error(request, error_message + str(err))

def validate_investigator(request, householdform, posted_locations):
    investigator_form = {'value': '', 'text': '', 'error': '',
                         'options': Investigator.objects.filter(location__in=posted_locations)}
    investigator = None
    try:
        investigator = Investigator.objects.get(id=int(request.POST['investigator']))
        investigator_form['text'] = investigator.name
        investigator_form['value'] = investigator.id
    except MultiValueDictKeyError:
        message = "No investigator provided."
        investigator_form['error'] = message
        householdform.errors['__all__'] = householdform.error_class([message])
    except (ObjectDoesNotExist, ValueError):
        investigator_form['text'] = request.POST['investigator']
        investigator_form['value'] = request.POST['investigator']
        message = "You provided an unregistered investigator."
        investigator_form['error'] = message
        householdform.errors['__all__'] = householdform.error_class([message])
    return investigator, investigator_form

def create_household(householdform, investigator, valid):
    is_valid_household = householdform['household'].is_valid()
    if investigator and is_valid_household:
        householdform['household'].instance.investigator = investigator
        householdform['household'].save()
        valid['household'] = True
    return valid

def create_remaining_modelforms(householdform, valid):
    if valid['household']:
        householdform['householdHead'].instance.household = householdform['household'].instance
        is_valid_form = householdform['householdHead'].is_valid()
        if is_valid_form:
            householdform['householdHead'].save()
            valid['householdHead'] = True
    return valid

def delete_created_modelforms(householdform, valid):
    for key in valid.keys():
        householdform[key].instance.delete()

def _process_form(householdform, investigator, request):
    valid = {}
    valid = create_household(householdform, investigator, valid)
    valid = create_remaining_modelforms(householdform, valid)

    if valid.values().count(True) == len(householdform.keys()):
        messages.success(request, "Household successfully registered.")
        return HttpResponseRedirect("/households/new")

    delete_created_modelforms(householdform, valid)
    _add_error_response_message(householdform, request)
    return None

def set_household_form(data):
    householdform = {}
    householdform['householdHead'] = HouseholdHeadForm(data=data, auto_id='household-%s', label_suffix='')
    householdform['household'] = HouseholdForm(data=data, auto_id='household-%s', label_suffix='')
    return householdform

def create(request, selected_location):
    householdform = set_household_form(data=request.POST)
    posted_locations = selected_location.get_descendants(include_self=True)
    investigator, investigator_form = validate_investigator(request, householdform['household'], posted_locations)
    response = _process_form(householdform, investigator, request)

    return response, householdform, investigator, investigator_form

@login_required
@permission_required('auth.can_view_households')
def new(request):
    selected_location = None
    response = None
    householdform = set_household_form(data=None)
    investigator_form = {'value': '', 'text': '', 'options': '', 'error': ''}
    month_choices= {'selected_text':'', 'selected_value':''}
    year_choices= {'selected_text':'', 'selected_value':''}

    if request.method == 'POST':
        selected_location = Location.objects.get(id=request.POST['location']) if contains_key(request.POST, 'location') else None
        response, householdform, investigator, investigator_form = create(request, selected_location)
        month_choices={'selected_text':MONTHS[int(request.POST['resident_since_month'])][1],
                        'selected_value':request.POST['resident_since_month']    }
        year_choices={'selected_text':request.POST['resident_since_year'],
                        'selected_value':request.POST['resident_since_year']    }

    householdHead = householdform['householdHead']
    del householdform['householdHead']
    return response or render(request, 'households/new.html', {'selected_location': selected_location,
                                                               'locations': LocationWidget(selected_location),
                                                               'investigator_form': investigator_form,
                                                               'headform': householdHead,
                                                               'householdform': householdform,
                                                               'months_choices': householdHead.resident_since_month_choices(month_choices),
                                                               'years_choices': householdHead.resident_since_year_choices(year_choices),
                                                               'action': "/households/new/",
                                                               'id': "create-household-form",
                                                               'button_label': "Create Household",
                                                               'loading_text': "Creating..."})
@login_required
def get_investigators(request):
    location = request.GET['location'] if request.GET.has_key('location') and request.GET['location'] else None
    investigators = Investigator.objects.filter(location=location)
    investigator_hash = {}
    for investigator in investigators:
        investigator_hash[investigator.name] = investigator.id
    return HttpResponse(json.dumps(investigator_hash), content_type="application/json")

@permission_required('auth.can_view_households')
def list_households(request):
    selected_location = None

    households = Household.objects.all().order_by('head__surname')

    params = request.GET
    if params.has_key('location') and params['location'].isdigit():
        selected_location = Location.objects.get(id=int(params['location']))
        corresponding_locations = selected_location.get_descendants(include_self=True)
        investigators = Investigator.objects.filter(location__in=corresponding_locations)
        households = Household.objects.filter(investigator__in=investigators).order_by('head__surname')

    households = Household.set_related_locations(households)
    if not households:
        location_type = selected_location.type.name.lower() if selected_location and selected_location.type else 'location'
        messages.error(request, "There are  no households currently registered  for this %s." % location_type)
    return render(request, 'households/index.html',
                  {'households': households, 'location_data': LocationWidget(selected_location), 'request': request})

def view_household(request, household_id):
    household = Household.objects.get(id=household_id)
    return render(request, 'households/show.html', {'household': household})
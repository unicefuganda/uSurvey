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


def create_household(householdform, investigator, valid, uid):
    is_valid_household = householdform['household'].is_valid()

    if investigator and is_valid_household:
        household = householdform['household'].save(commit=False)
        household.investigator = investigator
        household.location = investigator.location
        if uid:
            household.uid = uid
        household.save()
        valid['household'] = True
    return valid


def create_remaining_modelforms(householdform, valid):
    if valid.get('household', None):
        householdform['householdHead'].instance.household = householdform['household'].instance
        is_valid_form = householdform['householdHead'].is_valid()
        if is_valid_form:
            householdform['householdHead'].save()
            valid['householdHead'] = True
    return valid


def delete_created_modelforms(householdform, valid):
    for key in valid.keys():
        householdform[key].instance.delete()


def _process_form(householdform, investigator, request, is_edit=False, uid=None):
    valid = {}
    valid = create_household(householdform, investigator, valid, uid)

    if not is_edit:
        valid = create_remaining_modelforms(householdform, valid)

    if valid.values().count(True) == len(householdform.keys()):

        redirect_url = "/households/new"
        action_text = 'registered'
        if is_edit:
            action_text = 'edited'
            redirect_url = "/households/"

        messages.success(request, "Household successfully %s." % action_text)
        return HttpResponseRedirect(redirect_url)

    delete_created_modelforms(householdform, valid)
    _add_error_response_message(householdform, request)
    return None


def set_household_form(uid=None, data=None, is_edit=False, instance=None):
    householdform = {}
    if not is_edit:
        householdform['householdHead'] = HouseholdHeadForm(data=data, auto_id='household-%s', label_suffix='')

    householdform['household'] = HouseholdForm(data=data, instance=instance, is_edit=is_edit, uid=uid,
                                               auto_id='household-%s', label_suffix='')
    return householdform


def create(request, selected_location, instance=None, is_edit=False, uid=None):
    householdform = set_household_form(uid=uid, data=request.POST, instance=instance, is_edit=is_edit)
    posted_locations = selected_location.get_descendants(include_self=True)
    investigator, investigator_form = validate_investigator(request, householdform['household'], posted_locations)
    response = _process_form(householdform, investigator, request, is_edit=is_edit, uid=uid)

    return response, householdform, investigator, investigator_form


@login_required
@permission_required('auth.can_view_households')
def new(request):
    selected_location = None
    response = None
    householdform = set_household_form(data=None)
    investigator_form = {'value': '', 'text': '', 'options': '', 'error': ''}
    month_choices = {'selected_text': '', 'selected_value': ''}
    year_choices = {'selected_text': '', 'selected_value': ''}

    if request.method == 'POST':
        selected_location = Location.objects.get(id=request.POST['location']) if contains_key(request.POST,
                                                                                              'location') else None
        response, householdform, investigator, investigator_form = create(request, selected_location)
        month_choices = {'selected_text': MONTHS[int(request.POST['resident_since_month'])][1],
                         'selected_value': request.POST['resident_since_month']}
        year_choices = {'selected_text': request.POST['resident_since_year'],
                        'selected_value': request.POST['resident_since_year']}

    householdHead = householdform['householdHead']
    del householdform['householdHead']
    return response or render(request, 'households/new.html', {'selected_location': selected_location,
                                                               'locations': LocationWidget(selected_location),
                                                               'investigator_form': investigator_form,
                                                               'headform': householdHead,
                                                               'householdform': householdform,
                                                               'months_choices': householdHead.resident_since_month_choices(
                                                                   month_choices),
                                                               'years_choices': householdHead.resident_since_year_choices(
                                                                   year_choices),
                                                               'action': "/households/new/",
                                                               'heading': "New Household",
                                                               'id': "create-household-form",
                                                               'button_label': "Create",
                                                               'loading_text': "Creating..."})


@login_required
def get_investigators(request):
    location = request.GET['location'] if request.GET.has_key('location') and request.GET['location'] else None
    investigators = Investigator.objects.filter(location=location, is_blocked=False)
    investigator_hash = {}
    for investigator in investigators:
        investigator_hash[investigator.name] = investigator.id
    return HttpResponse(json.dumps(investigator_hash), content_type="application/json")


@permission_required('auth.can_view_households')
def list_households(request):
    selected_location = None

    all_households = Household.objects.all().order_by('household_member__householdhead__surname')
    households = list()
    map(lambda household: not household in households and households.append(household), all_households)

    params = request.GET
    if params.has_key('location') and params['location'].isdigit():
        selected_location = Location.objects.get(id=int(params['location']))
        corresponding_locations = selected_location.get_descendants(include_self=True)
        investigators = Investigator.objects.filter(location__in=corresponding_locations)
        households = Household.objects.filter(investigator__in=investigators)
    households = Household.set_related_locations(households)
    if not households:
        location_type = selected_location.type.name.lower() if selected_location and selected_location.type else 'location'
        messages.error(request, "There are  no households currently registered  for this %s." % location_type)

    return render(request, 'households/index.html',
                  {'households': households, 'location_data': LocationWidget(selected_location), 'request': request})


def view_household(request, household_id):
    household = Household.objects.get(id=household_id)
    return render(request, 'households/show.html', {'household': household})


def edit_household(request, household_id):
    household_selected = Household.objects.get(id=household_id)
    selected_location = household_selected.location
    response = None
    uid = household_selected.uid
    household_form = set_household_form(is_edit=True, instance=household_selected)
    investigators = Investigator.objects.filter(location=selected_location, is_blocked=False)
    investigator_form = {'value': '', 'text': '',
                         'options': investigators,
                         'error': ''}

    if request.method == 'POST':
        uid = request.POST.get('uid', None)

        selected_location = Location.objects.get(id=request.POST['location']) if contains_key(request.POST,
                                                                                              'location') else None
        response, household_form, investigator, investigator_form = create(request, selected_location,
                                                                           instance=household_selected, is_edit=True,
                                                                           uid=uid)
    return response or render(request, 'households/new.html', {'selected_location': selected_location,
                                                               'locations': LocationWidget(selected_location),
                                                               'investigator_form': investigator_form,
                                                               'householdform': household_form,
                                                               'action': "/households/%s/edit/" % household_id,
                                                               'id': "add-household-form",
                                                               'button_label': "Save",
                                                               'heading': "Edit Household",
                                                               'uid': uid,
                                                               'loading_text': "Updating...", 'is_edit': True})

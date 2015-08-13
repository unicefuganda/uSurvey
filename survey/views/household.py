import json

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, permission_required
from survey.models import Location, LocationType
from survey.forms.householdHead import *
from survey.forms.household import *
from survey.models import Survey, EnumerationArea
from survey.models.households import Household
from survey.models.interviewer import Interviewer
from survey.views.location_widget import LocationWidget
from survey.utils.views_helper import contains_key
from survey.utils.query_helper import get_filterset
from survey.forms.enumeration_area import EnumerationAreaForm, LocationsFilterForm


CREATE_HOUSEHOLD_DEFAULT_SELECT = ''


def _add_error_response_message(householdform, request):
    error_message = "Household not registered. "
    messages.error(request, error_message + "See errors below.")

    for key in householdform.keys():
        form = householdform[key]
        if form.non_field_errors():
            for err in form.non_field_errors():
                messages.error(request, error_message + str(err))


def validate_interviewer(request, householdform, selected_ea):
    interviewer_form = {'value': '', 'text': '', 'error': '',
                         'options': Interviewer.objects.filter(ea=selected_ea)}
    interviewer = None
    try:
        interviewer = Interviewer.objects.get(id=int(request.POST['interviewer']))
        interviewer_form['text'] = interviewer.name
        interviewer_form['value'] = interviewer.id
    except MultiValueDictKeyError:
        message = "No interviewer provided."
        interviewer_form['error'] = message
        householdform.errors['__all__'] = householdform.error_class([message])
    except (ObjectDoesNotExist, ValueError):
        interviewer_form['text'] = request.POST['interviewer']
        interviewer_form['value'] = request.POST['interviewer']
        message = "You provided an unregistered interviewer."
        interviewer_form['error'] = message
        householdform.errors['__all__'] = householdform.error_class([message])
    return interviewer, interviewer_form


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


def _process_form(householdform, interviewer, request, is_edit=False, uid=None):
    valid = {}
    valid = create_household(householdform, interviewer, valid, uid)

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
    household_form = {}
    if not is_edit:
        household_form['householdHead'] = HouseholdHeadForm(data=data, auto_id='household-%s', label_suffix='')
    open_survey = None #Survey.currently_open_survey()
    household_form['household'] = HouseholdForm(data=data, instance=instance, is_edit=is_edit, uid=uid,
                                                survey=open_survey, auto_id='household-%s', label_suffix='')
    return household_form


def create(request, selected_ea, instance=None, is_edit=False, uid=None):
    household_form = set_household_form(uid=uid, data=request.POST, instance=instance, is_edit=is_edit)
    interviewer, interviewer_form = validate_interviewer(request, household_form['household'], selected_ea)
    response = _process_form(household_form, interviewer, request, is_edit=is_edit, uid=uid)
    return response, household_form, interviewer, interviewer_form


@login_required
@permission_required('auth.can_view_households')
def new(request):
    selected_location = None
    selected_ea = None
    response = None

    householdform = set_household_form(data=None)
    interviewer_form = {'value': '', 'text': '', 'options': '', 'error': ''}
    month_choices = {'selected_text': '', 'selected_value': ''}
    year_choices = {'selected_text': '', 'selected_value': ''}

    if request.method == 'POST':
        selected_ea = EnumerationArea.objects.get(id=request.POST['ea']) if contains_key(request.POST, 'ea') else None
        if selected_ea:
            selected_location = selected_ea.locations.all()
            if selected_location:
                selected_location = selected_location[0]
        response, householdform, interviewer, interviewer_form = create(request, selected_ea)

    household_head = householdform['householdHead']

    del householdform['householdHead']
    context = {'selected_location': selected_location,
               'locations': LocationWidget(selected_location, ea=selected_ea),
               'interviewer_form': interviewer_form,
               'headform': household_head,
               'householdform': householdform,
               'action': "/households/new/",
               'heading': "New Household",
               'id': "create-household-form",
               'button_label': "Create",
               'loading_text': "Creating..."}
    return response or render(request, 'households/new.html', context)


@login_required
def get_interviewers(request):
    ea = request.GET['ea'] if request.GET.has_key('ea') and request.GET['ea'] else None
    interviewers = Interviewer.objects.filter(ea=ea, is_blocked=False)
    interviewer_hash = {}
    for interviewer in interviewers:
        interviewer_hash[interviewer.name] = interviewer.id
    return HttpResponse(json.dumps(interviewer_hash), content_type="application/json")


def _remove_duplicates(all_households):
    households_without_heads = list(all_households.filter(household_member__householdhead__surname=None).distinct())
    households = list(all_households.exclude(household_member__householdhead__surname=None).distinct('household_member__householdhead__surname'))
    households.extend(households_without_heads)
    return households


@permission_required('auth.can_view_households')
def list_households(request):
    locations_filter = LocationsFilterForm(request.GET, include_ea=True)
    enumeration_areas = locations_filter.get_enumerations()
    all_households = Household.objects.filter(ea__in=enumeration_areas).order_by('household_member__householdhead__surname')
    search_fields = [ 'ea__name', 'registrar__name', 'survey__name', ]
    if request.GET.has_key('q'):
        all_households = get_filterset(all_households, request.GET['q'], search_fields)
    households = _remove_duplicates(all_households)
    if not households:
        messages.error(request, "There are  no households currently registered for present location" )
    return render(request, 'households/index.html',
                  {'households': households, 
                   'locations_filter' : locations_filter, 
                   'location_filter_types' : LocationType.objects.exclude(pk=LocationType.smallest_unit().pk),
                   'Largest Unit' : LocationType.largest_unit(),
                   'request': request})

@permission_required('auth.can_view_batches')
def household_filter(request):
    locations_filter = LocationsFilterForm(request.GET, include_ea=True)
    enumeration_areas = locations_filter.get_enumerations()
    all_households = Household.objects.filter(ea__in=enumeration_areas).order_by('household_member__householdhead__surname')
    search_fields = [ 'ea__name', 'registrar__name', 'survey__name', ]
    if request.GET.has_key('q'):
        all_households = get_filterset(all_households, request.GET['q'], search_fields)
    all_households =  all_households.values('id', 'house_number', ).order_by('name')
    json_dump = json.dumps(list(all_households), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')

def view_household(request, household_id):
    household = Household.objects.get(id=household_id)
    return render(request, 'households/show.html', {'household': household})

def edit_household(request, household_id):
    household_selected = Household.objects.get(id=household_id)
    selected_location = household_selected.location
    selected_ea = household_selected.ea
    response = None
    uid = household_selected.uid
    household_form = set_household_form(is_edit=True, instance=household_selected)
    interviewers = Interviewer.objects.filter(ea=selected_ea, is_blocked=False)
    interviewer_form = {'value': '', 'text': '',
                         'options': interviewers,
                         'error': ''}

    if request.method == 'POST':
        uid = request.POST.get('uid', None)

        selected_location = Location.objects.get(id=request.POST['location']) if contains_key(request.POST,
                                                                                              'location') else None
        selected_ea = EnumerationArea.objects.get(id=request.POST['ea']) if contains_key(request.POST, 'ea') else None
        response, household_form, interviewer, interviewer_form = create(request, selected_location,
                                                                           instance=household_selected, is_edit=True,
                                                                           uid=uid)
    return response or render(request, 'households/new.html', {'selected_location': selected_location,
                                                               'locations': LocationWidget(selected_location, ea=selected_ea),
                                                               'interviewer_form': interviewer_form,
                                                               'householdform': household_form,
                                                               'action': "/households/%s/edit/" % household_id,
                                                               'id': "add-household-form",
                                                               'button_label': "Save",
                                                               'heading': "Edit Household",
                                                               'uid': uid,
                                                               'loading_text': "Updating...", 'is_edit': True})

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, permission_required
from survey.models import Location, LocationType, SurveyAllocation, SurveyHouseholdListing
from survey.forms.householdHead import *
from survey.forms.household import *
from survey.models import Survey, EnumerationArea
from survey.models.households import Household
from survey.models.interviewer import Interviewer
from survey.views.location_widget import LocationWidget
from survey.utils.views_helper import contains_key
from survey.utils.query_helper import get_filterset
from django.core.urlresolvers import reverse
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


@login_required
@permission_required('auth.can_view_households')
def new(request):
    return save(request, instance=None)


@login_required
def get_interviewers(request):
    ea = request.GET['ea'] if request.GET.has_key(
        'ea') and request.GET['ea'] else None
    interviewers = Interviewer.objects.filter(ea=ea, is_blocked=False)
    interviewer_hash = {}
    for interviewer in interviewers:
        interviewer_hash[interviewer.name] = interviewer.id
    return HttpResponse(json.dumps(interviewer_hash), content_type="application/json")


@permission_required('auth.can_view_households')
def list_households(request):
    locations_filter = LocationsFilterForm(data=request.GET, include_ea=True)
    enumeration_areas = locations_filter.get_enumerations()
    households = Household.objects.filter(
        listing__ea__in=enumeration_areas).order_by('house_number')
    search_fields = ['house_number', 'listing__ea__name',
                     'last_registrar__name', 'listing__initial_survey__name', ]
    if request.GET.has_key('q'):
        households = get_filterset(households, request.GET['q'], search_fields)
    return render(request, 'households/index.html',
                  {'households': households,
                   'locations_filter': locations_filter,
                   'location_filter_types': LocationType.in_between(),
                   'Largest Unit': LocationType.largest_unit(),
                   'placeholder': 'house no, ea, survey, interviewer',
                   'request': request})


@permission_required('auth.can_view_batches')
def household_filter(request):
    locations_filter = LocationsFilterForm(request.GET, include_ea=True)
    enumeration_areas = locations_filter.get_enumerations()
    all_households = Household.objects.filter(ea__in=enumeration_areas).order_by(
        'household_member__householdhead__surname')
    search_fields = ['house_number', 'listing__ea__name',
                     'last_registrar__name', 'listing__initial_survey__name', ]
    if request.GET.has_key('q'):
        all_households = get_filterset(
            all_households, request.GET['q'], search_fields)
    all_households = all_households.values(
        'id', 'house_number', ).order_by('name')
    json_dump = json.dumps(list(all_households), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')


def view_household(request, household_id):
    household = Household.objects.get(id=household_id)
    request.breadcrumbs([
        ('Households', reverse('list_household_page')),
    ])
    return render(request, 'households/show.html', {'household': household})


def edit_household(request, household_id):
    household_selected = Household.objects.get(id=household_id)
    return save(request, instance=household_selected)


def save(request, instance=None):
    head = None
    if instance:
        handler = reverse('edit_household_page', args=(instance.pk, ))
        head = instance.get_head()
        heading = 'Edit Household'
        cancel_url = reverse('view_household_page', args=(instance.pk, ))
    else:
        handler = reverse('new_household_page')
        heading = 'New Household'
        cancel_url = reverse('list_household_page')
    locations_filter = LocationsFilterForm(data=request.GET, include_ea=True)
    householdform = HouseholdForm(
        instance=instance, eas=locations_filter.get_enumerations())
    headform = HouseholdHeadForm(instance=head)
    if request.method == 'POST':
        householdform = HouseholdForm(data=request.POST, instance=instance)
        headform = HouseholdHeadForm(data=request.POST, instance=head)
        if householdform.is_valid():
            household = householdform.save(commit=False)
            interviewer = household.last_registrar
            survey = SurveyAllocation.get_allocation(interviewer)
            if survey:
                survey_listing = SurveyHouseholdListing.get_or_create_survey_listing(
                    interviewer, survey)
                household.listing = survey_listing.listing
                household.save()
                householdform = HouseholdForm()
                # import pdb; pdb.set_trace()
                if headform.is_valid():
                    head = headform.save(commit=False)
                    head.household = household
                    head.registrar = interviewer
                    head.survey_listing = survey_listing
                    head.registration_channel = WebAccess.choice_name()
                    head.save()
                    if household.head_desc is not head.surname:
                        household.head_desc = head.surname
                        household.save()
                    messages.info(
                        request, 'Household %s saved successfully' % household.house_number)
                    return HttpResponseRedirect(reverse('view_household_page', args=(household.pk, )))
                handler = reverse('new_household_page')
            else:
                messages.error(request, 'No open survey for %s' %
                               interviewer.name)
    context = {
        'headform': headform,
        'householdform': householdform,
        'action': handler,
        'cancel_url': cancel_url,
        'heading': heading,
        'id': "create-household-form",
        'button_label': "Save",
        'loading_text': "Creating...",
        'locations_filter': locations_filter}
    request.breadcrumbs([
        ('Households', reverse('list_household_page')),
    ])
    return render(request, 'households/new.html', context)


@permission_required('auth.can_view_households')
def download_households(request):
    filename = 'all_households'
    header_keyval = settings.HOUSEHOLD_EXPORT_HEADERS
    # locations_filter = LocationsFilterForm(data=request.GET, include_ea=True)
    # household_details = Household.objects.filter(
    #     listing__ea=locations_filter.get_enumerations()
    # ).order_by('listing__ea', 'house_number').values(*header_keyval.values())
    household_details = Household.objects.all().order_by(
        'listing__ea', 'house_number').values(*header_keyval.values())
    headers = header_keyval.keys()

    def pretty_print(header, entry):
        if header == 'head_sex':
            return 'M' if int(entry[header]) == 1 else 'F'
        return unicode(entry[header]).encode('utf8').replace(',', '-')
    hd_response = [','.join(headers), ]
    for detail in household_details:
        vals = ','.join([pretty_print(header_keyval[header], detail)
                         for header in headers])
        hd_response.append(vals)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    response.write("\r\n".join(hd_response))
    return response

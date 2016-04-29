import json, ast
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from survey.models import Location, LocationType
from survey.forms.enumeration_area import LocationsFilterForm as LocFilterForm
from survey.forms.filters import LocationFilterForm
from survey.models import Survey, Interviewer, SurveyAllocation, Household, Batch, EnumerationArea
from survey.services.completion_rates_calculator import BatchLocationCompletionRates, \
    BatchHighLevelLocationsCompletionRates, BatchSurveyCompletionRates
from survey.views.location_widget import LocationWidget
from survey.utils.views_helper import contains_key, is_not_digit_nor_empty
from survey.utils.query_helper import get_filterset
from django.core.urlresolvers import reverse
from survey.services.results_download_service import ResultsDownloadService
import redis



def is_valid(params):
    if not contains_key(params, 'batch'):
        return False
    if is_not_digit_nor_empty(params, 'location'):
        return False
    if is_not_digit_nor_empty(params, 'ea'):
        return False
    return True


@login_required
@permission_required('auth.can_view_aggregates')
def survey_completion_summary(request, household_id, batch_id):
    household = get_object_or_404(Household, pk=household_id)
    batch = get_object_or_404(Batch, pk=batch_id)
    survey = batch.survey
    ea = household.listing.ea
    allocations = SurveyAllocation.objects.filter(allocation_ea=ea, survey=batch.survey)
    context = {}
    if allocations.exists():
        completion_rates = BatchLocationCompletionRates(batch, ea=ea, specific_households=[household_id, ])
        result_service = ResultsDownloadService(batch=batch, specific_households=[household_id, ])
        reports = result_service.generate_report()
        reports_headers = reports.pop(0)
        context.update({
        'household' : household,
        'batch': batch,
        'reports_headers': reports_headers,
        'reports': reports,
        'completion_rates': completion_rates,
        'interviewer': allocations[0].interviewer
        })
    request.breadcrumbs([
        ('Completion Rates', reverse('survey_completion_rates', )),
        ('EA Completion', reverse('ea_completion_summary', args=(ea.pk, batch.pk))),
    ])
    return render(request, 'aggregates/household_completion_report.html', context)

@login_required
@permission_required('auth.can_view_aggregates')
def ea_completion_summary(request, ea_id, batch_id):
    ea = get_object_or_404(EnumerationArea, pk=ea_id)
    batch = get_object_or_404(Batch, pk=batch_id)
    return render_household_details(request, ea.locations.all()[0], batch, ea.pk)

@login_required
@permission_required('auth.can_view_aggregates')
def location_completion_summary(request, location_id, batch_id):
    location = get_object_or_404(Location, pk=location_id)
    batch = get_object_or_404(Batch, pk=batch_id)
    return render_household_details(request, location, batch)


def render_household_details(request, location, batch, ea=None):
    context = { 'batch': batch}
    request.breadcrumbs([
        ('Completion Rates', reverse('survey_completion_rates', )),
    ])
    if ea:
        ea = get_object_or_404(EnumerationArea, pk=ea)
        context['selected_ea'] =  ea
        allocations = SurveyAllocation.objects.filter(allocation_ea=ea, survey=batch.survey)
        if allocations.exists():
            context['interviewer'] = allocations[0].interviewer
        location = ea.locations.all()[0]
    completion_rates = BatchLocationCompletionRates(batch, location=location, ea=ea)
    context.update({'completion_rates' : completion_rates, 'location' : location });
    return render(request, 'aggregates/household_completion_status.html', context)

def __get_parent_level_locations():
    return Location.objects.filter(type=LocationType.largest_unit())

@login_required
@permission_required('auth.can_view_aggregates')
def show(request):
    selected_location = None
    location_filter_form = LocationFilterForm()
    content = {'action': 'survey_completion_rates',
               'request': request}
    locations_filter = LocFilterForm(data=request.POST, include_ea=True)
    if request.method == 'POST':
        location_filter_form = LocationFilterForm(request.POST)
        if location_filter_form.is_valid():
            batch = location_filter_form.cleaned_data.get('batch', None)
            content['selected_batch'] = batch
            selected_location = locations_filter.last_location_selected
            selected_ea = request.POST.get('enumeration_area', None)
            if selected_ea:
                return render_household_details(request, selected_location, batch, selected_ea)
            if selected_location:
                high_level_locations = selected_location.get_children().order_by('name')
                content['selection_location_type'] = LocationType.objects.get(parent=selected_location.type)
            else:
                high_level_locations = __get_parent_level_locations()
            content['completion_rates'] = BatchHighLevelLocationsCompletionRates(batch, high_level_locations)
    content['locations_filter'] = locations_filter
    content['filter'] = location_filter_form
    return render(request, 'aggregates/completion_status.html', content)


def completion_json(request, survey_id):
    r_server = redis.Redis()
    key = "/usurvey/completion_rates/%s" %str(survey_id)
    json_dump=r_server.get(key)
    print json_dump
    return HttpResponse(json_dump, content_type='application/json')

@login_required
@permission_required('survey.view_completed_survey')
def show_interviewer_completion_summary(request):
    params = request.GET
    selected_location = None
    selected_ea = None
    interviewers = Interviewer.objects.order_by('id')
    search_fields = ['name', 'ea__name']
    if request.GET.has_key('q'):
        interviewers = get_filterset(interviewers, request.GET['q'], search_fields)
    if params.has_key('status'):
        interviewers = interviewers.intervieweraccess.filter(is_active=ast.literal_eval(params['status']))
    locations_filter = LocFilterForm(data=request.GET, include_ea=True)
    if locations_filter.is_valid():
        print 'locations count: ', locations_filter.get_enumerations().count()
        interviewers = interviewers.filter(ea__in=locations_filter.get_enumerations()).order_by('name')
    return render(request, 'aggregates/interviewers_summary.html',
                  {'interviewers': interviewers,
                    'locations_filter' : locations_filter,
                   'request': request})


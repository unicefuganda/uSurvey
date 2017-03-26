import json
import ast
from django.contrib.auth.decorators import login_required, permission_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from survey.models import Indicator
from survey.models import Location
from survey.models import LocationType
from survey.forms.enumeration_area import LocationsFilterForm as LocFilterForm
from survey.forms.filters import LocationFilterForm
from survey.models import Survey, Interviewer, SurveyAllocation, Household, Batch, EnumerationArea, Interview
from survey.services.completion_rates_calculator import BatchLocationCompletionRates, \
    BatchHighLevelLocationsCompletionRates, BatchSurveyCompletionRates
from survey.utils.views_helper import contains_key, is_not_digit_nor_empty
from survey.utils.query_helper import get_filterset
from django.core.urlresolvers import reverse
from survey.services.results_download_service import ResultsDownloadService
from cacheops import cached_as
from django.conf import settings


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
    batch.survey
    ea = household.listing.ea
    allocations = SurveyAllocation.objects.filter(
        allocation_ea=ea, survey=batch.survey)
    context = {}
    if allocations.exists():
        completion_rates = BatchLocationCompletionRates(
            batch, ea=ea, specific_households=[household_id, ])
        result_service = ResultsDownloadService(batch=batch, specific_households=[household_id, ])
        reports = result_service.generate_interview_reports()
        reports_headers = reports.pop(0)
        context.update({
            'household': household,
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
    context = {'batch': batch}
    request.breadcrumbs([
        ('Completion Rates', reverse('survey_completion_rates', )),
    ])
    if ea:
        ea = get_object_or_404(EnumerationArea, pk=ea)
        context['selected_ea'] = ea
        allocations = SurveyAllocation.objects.filter(
            allocation_ea=ea, survey=batch.survey)
        if allocations.exists():
            context['interviewer'] = allocations[0].interviewer
        location = ea.locations.all()[0]
    completion_rates = BatchLocationCompletionRates(
        batch, location=location, ea=ea)
    context.update(
        {'completion_rates': completion_rates, 'location': location})
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
                content['selection_location_type'] = LocationType.objects.get(
                    parent=selected_location.type)
            else:
                high_level_locations = __get_parent_level_locations()
            content['completion_rates'] = BatchHighLevelLocationsCompletionRates(
                batch, high_level_locations)
    content['locations_filter'] = locations_filter
    content['filter'] = location_filter_form
    return render(request, 'aggregates/completion_status.html', content)


@login_required
@permission_required('auth.can_view_aggregates')
def completion_json(request, survey_id):
    @cached_as(Survey.objects.filter(id=survey_id))
    def get_result_json():
        """Basically if survey is sampled and we are now in batch collection phase, display percentage completion.
        For listing or census data collection, just show count
        :return:
        """
        survey = Survey.objects.get(id=survey_id)
        country = LocationType.objects.get(parent__isnull=True)
        if hasattr(settings, 'MAP_ADMIN_LEVEL'):
            location_type = country.get_descendants()[settings.MAP_ADMIN_LEVEL - 1]
        else:
            location_type = LocationType.largest_unit()
        completion_rates = {}
        survey.has_sampling
        survey.is_open()
        #basically get interviews count
        for location in location_type.locations.all():
            total_eas = EnumerationArea.under_(location).count()
            total_interviews = Interview.interviews_in(location, survey).distinct('id').count()
            active_eas = Interview.interviews_in(location, survey).distinct('ea').count()
            indicator_value = float(total_interviews) / total_eas
            completion_rates[location.name.upper()] = {'value': '{0:.2f}'.format(indicator_value),
                                                       'total_eas': total_eas,
                                                       'active_eas': active_eas,
                                                       'per_active_ea': '{0:.2f}'.format(float(total_interviews)/
                                                                                         (active_eas or 1.0)),
                                                       'total_interviews': total_interviews}
        return json.dumps(completion_rates, cls=DjangoJSONEncoder)
    json_dump = get_result_json()
    return HttpResponse(json_dump, content_type='application/json')



@login_required
@permission_required('auth.can_view_aggregates')
def json_summary(request):
    request_data = request.GET if request.method == 'GET' else request.POST
    survey_id = request_data['survey']
    return completion_json(request, survey_id)


@login_required
@permission_required('auth.can_view_aggregates')
def survey_parameters(request):
    indicator = Indicator.get(id=request.GET['indicator'])
    parameters = []
    map(lambda opt: parameters.append({'id': opt.id, 'name': opt.text}), indicator.parameter.options.all())
    return HttpResponse(json.dumps(parameters),
                        content_type='application/json')

@login_required
@permission_required('auth.can_view_aggregates')
def survey_indicators(request):
    survey = Survey.get(id=request.GET['survey'])
    indicators = []
    for batch in survey.batches.all():
        for question in batch.questions.all():
            map(lambda indicator: indicators.append({'id': indicator.id, 'name': indicator.name}),
                Indicator.objects.filter(parameter__id=question.id))
    return HttpResponse(json.dumps(indicators),
                        content_type='application/json')


@login_required
@permission_required('survey.view_completed_survey')
def show_interviewer_completion_summary(request):
    params = request.GET
    interviewers = Interviewer.objects.order_by('id')
    search_fields = ['name', 'ea__name']
    if request.GET.has_key('q'):
        interviewers = get_filterset(
            interviewers, request.GET['q'], search_fields)
    if params.has_key('status'):
        interviewers = interviewers.intervieweraccess.filter(
            is_active=ast.literal_eval(params['status']))
    locations_filter = LocFilterForm(data=request.GET, include_ea=True)
    if locations_filter.is_valid():
        # print 'locations count: ',
        # locations_filter.get_enumerations().count()
        interviewers = interviewers.filter(
            ea__in=locations_filter.get_enumerations()).order_by('name')
    return render(request, 'aggregates/interviewers_summary.html',
                  {'interviewers': interviewers,
                   'locations_filter': locations_filter,
                   'request': request})

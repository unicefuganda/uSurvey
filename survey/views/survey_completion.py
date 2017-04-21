import json
import ast
from django.contrib import messages
from django.utils.datastructures import SortedDict
from django.contrib.auth.decorators import login_required, permission_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from survey.models import Location, LocationType, Indicator,\
    Answer, QuestionOption
from survey.forms.enumeration_area import LocationsFilterForm as LocFilterForm
from survey.forms.filters import LocationFilterForm
from survey.models import Survey, Interviewer, SurveyAllocation,\
    Batch, EnumerationArea, Interview

from survey.views.location_widget import LocationWidget
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


def __get_parent_level_locations():
    return Location.objects.filter(type=LocationType.largest_unit())


@login_required
@permission_required('auth.can_view_aggregates')
def indicators_json(request):
    in_kwargs = {'display_on_dashboard': True}
    if request.GET.get('survey'):
        in_kwargs['survey__id'] = request.GET['survey']
    indicators = Indicator.objects.filter(**in_kwargs).order_by('name')

    @cached_as(indicators)
    def get_result_json():
        """Basically fetch all indicators as per the map level info
        :return:
        """
        indicator_details = {}
        country = LocationType.objects.get(parent__isnull=True)
        if hasattr(settings, 'MAP_ADMIN_LEVEL'):
            location_type = country.get_descendants()[
                settings.MAP_ADMIN_LEVEL - 1]
        else:
            location_type = LocationType.largest_unit()
        for indicator in indicators:
            indicator_df = indicator.get_data(
                location_type.locations.all()).fillna(
                value='null')
            indicator_df.index = indicator_df.index.str.upper()
            indicator_details[indicator.name] = indicator_df.transpose(
            ).to_dict()
        return json.dumps(indicator_details, cls=DjangoJSONEncoder)
    json_dump = get_result_json()
    return HttpResponse(json_dump, content_type='application/json')


@login_required
@permission_required('auth.can_view_aggregates')
def completion_json(request, survey_id):
    @cached_as(Survey.objects.filter(id=survey_id))
    def get_result_json():
        """Basically if survey is sampled and we are\
            now in batch collection phase, display percentage completion.
        For listing or census data collection, just show count
        :return:
        """
        survey = Survey.objects.get(id=survey_id)
        country = LocationType.objects.get(parent__isnull=True)
        if hasattr(settings, 'MAP_ADMIN_LEVEL'):
            location_type = country.get_descendants()[
                settings.MAP_ADMIN_LEVEL - 1]
        else:
            location_type = LocationType.largest_unit()
        divider = 1.0
        completion_rates = {}
        has_sampling = survey.has_sampling
        is_open = survey.is_open()
        # basically get interviews count
        for location in location_type.locations.all():
            description = 'Percentage Responses'
            total_eas = EnumerationArea.under_(location).count()
            total_interviews = Interview.interviews_in(
                location, survey).distinct('id').count()
            active_eas = Interview.interviews_in(
                location, survey).distinct('ea').count()
            indicator_value = float(total_interviews) / total_eas
            completion_rates[location.name.upper()] = {
                'value': '{0:.2f}'.format(indicator_value),
                'total_eas': total_eas,
                'active_eas': active_eas,
                'per_active_ea': '{0:.2f}'.format(
                    float(
                        total_interviews)/(active_eas or 1.0)),
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
    map(lambda opt: parameters.append(
        {'id': opt.id, 'name': opt.text}), indicator.parameter.options.all())
    return HttpResponse(json.dumps(parameters),
                        content_type='application/json')


@login_required
@permission_required('auth.can_view_aggregates')
def survey_indicators(request):
    survey = Survey.get(id=request.GET['survey'])
    indicators = []
    for batch in survey.batches.all():
        for question in batch.questions.all():
            map(lambda indicator: indicators.append(
                {
                    'id': indicator.id,
                    'name': indicator.name
                }),
                Indicator.objects.filter(parameter__id=question.id))
    return HttpResponse(json.dumps(indicators),
                        content_type='application/json')


@login_required
@permission_required('survey.view_completed_survey')
def show_interviewer_completion_summary(request):
    params = request.GET
    selected_location = None
    selected_ea = None
    interviewers = Interviewer.objects.order_by('id')
    search_fields = ['name', 'ea__name']
    if 'q' in request.GET:
        interviewers = get_filterset(
            interviewers, request.GET['q'], search_fields)
    if 'status' in params:
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

import json
import ast
from django.contrib import messages
from django.utils.datastructures import SortedDict
from django.contrib.auth.decorators import login_required, permission_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from survey.models import Location, LocationType, Indicator,\
    Answer, QuestionOption
from survey.forms.enumeration_area import LocationsFilterForm as LocFilterForm
from survey.forms.filters import LocationFilterForm
from survey.models import Survey, Interviewer, SurveyAllocation,\
    Batch, EnumerationArea, Interview
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
    report_level = None
    if request.GET.get('survey'):
        in_kwargs['survey__id'] = request.GET['survey']
    if request.GET.get('report_level'):
        report_level = int(request.GET['report_level'])
    indicators = Indicator.objects.filter(**in_kwargs).order_by('name')

    @cached_as(indicators, extra=(report_level, ))
    def get_result_json():
        """Basically fetch all indicators as per the map level info
        :return:
        """
        indicator_details = {}
        country = Location.country()
        if hasattr(settings, 'MAP_ADMIN_LEVEL'):
            location_type = country.get_descendants()[settings.MAP_ADMIN_LEVEL - 1]
        else:
            location_type = LocationType.largest_unit()
        if report_level is None:
            lreport_level = location_type.level
        else:
            lreport_level = report_level
        for indicator in indicators:
            indicator_df = indicator.get_data(country, report_level=lreport_level).fillna(0)
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
        survey = get_object_or_404(Survey, pk=survey_id)
        country_type = LocationType.objects.get(parent__isnull=True)
        hierachy_count = country_type.get_descendant_count()
        if hasattr(settings, 'MAP_ADMIN_LEVEL'):
            location_type = country_type.get_descendants()[settings.MAP_ADMIN_LEVEL - 1]
        else:
            location_type = LocationType.largest_unit()
        divider = 1.0
        completion_rates = {}
        has_sampling = survey.has_sampling
        is_open = survey.is_open()
        parent_loc = 'locations'
        for i in range(hierachy_count - location_type.level):    # fetches direct descendants from ea__locations
            parent_loc = '%s__parent' % parent_loc
        total_interviews = dict(Interview.objects.filter(**{'survey': survey
                                                            }).values_list('ea__%s__name' % parent_loc
                                                                           ).annotate(total=Count('id', distinct=True)))
        total_eas = dict(EnumerationArea.objects.all().values_list('%s__name' % parent_loc
                                                                   ).annotate(total=Count('id', distinct=True)))
        active_eas = dict(Interview.objects.filter(**{'survey': survey,
                                                      }).values_list('ea__%s__name' % parent_loc
                                                           ).annotate(total=Count('ea', distinct=True)))
        # basically get interviews count
        for location in location_type.locations.all():
            type_total_eas = total_eas.get(location.name, 0)
            type_total_interviews = total_interviews.get(location.name, 0)
            type_active_eas = active_eas.get(location.name, 0)
            indicator_value = float(type_total_interviews) / type_total_eas
            completion_rates[location.name.upper()] = {
                'value': '{0:.2f}'.format(indicator_value),
                'total_eas': type_total_eas,
                'active_eas': type_active_eas,
                'is_open': survey.is_open_for(location),
                'per_active_ea': '{0:.2f}'.format(float(type_total_interviews)/(type_active_eas or 1.0)),
                'total_interviews': type_total_interviews,
            }
        return json.dumps(completion_rates, cls=DjangoJSONEncoder)
    json_dump = get_result_json()
    return HttpResponse(json_dump, content_type='application/json')


@login_required
@permission_required('auth.can_view_aggregates')
def json_summary(request):
    request_data = request.GET if request.method == 'GET' else request.POST
    survey_id = request_data['survey']
    return completion_json(request, survey_id)


# @login_required
# @permission_required('auth.can_view_aggregates')
# def survey_parameters(request):
#     indicator = get_object_or_404(Indicator, pk=request.GET['indicator'])
#     parameters = []
#     try:
#         map(lambda opt: parameters.append(
#         {'id': opt.id, 'name': opt.text}), indicator.parameter.options.all())
#     except Exception as e:
#         pass
#     return HttpResponse(json.dumps(parameters),
#                         content_type='application/json')


@login_required
@permission_required('auth.can_view_aggregates')
def survey_indicators(request):
    survey = get_object_or_404(Survey, pk=request.GET['survey'])
    indicators = []    
    indicators_list = Indicator.objects.filter(survey=survey)
    map(lambda indicator: indicators.append(
                {
                    'id': indicator.id,
                    'name': indicator.name
                }),
                indicators_list
                )
    return HttpResponse(json.dumps(indicators),
                        content_type='application/json')


@login_required
@permission_required('auth.view_completed_survey')
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

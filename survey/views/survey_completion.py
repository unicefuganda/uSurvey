import json, ast
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from survey.models import Location, LocationType
from survey.forms.enumeration_area import LocationsFilterForm as LocFilterForm
from survey.forms.filters import LocationFilterForm
from survey.models import Survey, Interviewer, SurveyAllocation
from survey.services.completion_rates_calculator import BatchLocationCompletionRates, \
    BatchHighLevelLocationsCompletionRates, BatchSurveyCompletionRates
from survey.views.location_widget import LocationWidget
from survey.utils.views_helper import contains_key, is_not_digit_nor_empty
from survey.utils.query_helper import get_filterset


def is_valid(params):
    if not contains_key(params, 'batch'):
        return False
    if is_not_digit_nor_empty(params, 'location'):
        return False
    if is_not_digit_nor_empty(params, 'ea'):
        return False
    return True


def render_household_details(request, location, ea, batch):
    context = {'selected_ea': ea}
    allocations = SurveyAllocation.objects.filter(allocation_ea=ea, survey=batch.survey)
    if not allocations.exists():
        messages.error(request, 'No interviewer registered for this ea.')
        return render(request, 'aggregates/household_completion_status.html', context)
    completion_rates = BatchLocationCompletionRates(batch, location=location, ea=ea)
    context.update({'completion_rates': completion_rates,
                    'interviewer': allocations[0].interviewer})
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
            selected_location = locations_filter.last_location_selected
            selected_ea = request.POST.get('enumeration_area', None)
            if selected_ea:
                return render_household_details(request, selected_location, selected_ea, batch)
            if selected_location:
                high_level_locations = selected_location.get_children().order_by('name')
            else:
                high_level_locations = __get_parent_level_locations()
            content['completion_rates'] = BatchHighLevelLocationsCompletionRates(batch, high_level_locations)
    content['locations_filter'] = locations_filter
    content['filter'] = location_filter_form
    return render(request, 'aggregates/completion_status.html', content)


def completion_json(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    location_type = LocationType.largest_unit()
    completion_rates = BatchSurveyCompletionRates(location_type).get_completion_formatted_for_json(survey)
    json_dump = json.dumps(completion_rates, cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')

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
    # location_widget = LocationWidget(selected_location, ea=selected_ea)
    return render(request, 'aggregates/interviewers_summary.html',
                  {'interviewers': interviewers,
                    'locations_filter' : locations_filter,
                   'request': request})


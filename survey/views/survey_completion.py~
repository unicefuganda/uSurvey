import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from rapidsms.contrib.locations.models import Location, LocationType

from survey.forms.filters import LocationFilterForm
from survey.models import Survey, Investigator
from survey.services.completion_rates_calculator import BatchLocationCompletionRates, \
    BatchHighLevelLocationsCompletionRates, BatchSurveyCompletionRates
from survey.views.location_widget import LocationWidget
from survey.utils.views_helper import contains_key, is_not_digit_nor_empty


def is_valid(params):
    if not contains_key(params, 'batch'):
        return False
    if is_not_digit_nor_empty(params, 'location'):
        return False
    if is_not_digit_nor_empty(params, 'ea'):
        return False
    return True


def render_household_details(request, ea, batch):
    context = {'selected_ea': ea}
    investigator = Investigator.objects.filter(ea=ea)
    if not investigator.exists():
        messages.error(request, 'Investigator not registered for this ea.')
        return render(request, 'aggregates/household_completion_status.html', context)
    completion_rates = BatchLocationCompletionRates(batch, location=None, ea=ea)
    context.update({'completion_rates': completion_rates,
                    'investigator': investigator[0]})
    return render(request, 'aggregates/household_completion_status.html', context)


def __get_parent_level_locations():
    country = LocationType.objects.filter(name__iexact='country')
    if country:
        return Location.objects.filter(tree_parent__type=country[0]).order_by('name')

    return Location.objects.filter(tree_parent=None).order_by('name')


@login_required
@permission_required('auth.can_view_aggregates')
def show(request):
    selected_location = None
    location_filter_form = LocationFilterForm()
    content = {'action': 'survey_completion_rates',
               'request': request}
    if request.method == 'POST':
        location_filter_form = LocationFilterForm(request.POST)
        if location_filter_form.is_valid():
            batch = location_filter_form.cleaned_data.get('batch', None)
            selected_location = location_filter_form.cleaned_data.get('location', None)
            selected_ea = location_filter_form.cleaned_data.get('ea', None)
            if selected_ea:
                return render_household_details(request, selected_ea, batch)
            if selected_location:
                high_level_locations = selected_location.get_children().order_by('name')
            else:
                high_level_locations = __get_parent_level_locations()
            content['completion_rates'] = BatchHighLevelLocationsCompletionRates(batch, high_level_locations)
    content['locations'] = LocationWidget(selected_location)
    content['filter'] = location_filter_form
    return render(request, 'aggregates/completion_status.html', content)


def completion_json(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    location_type = LocationType.objects.get(name='District')
    completion_rates = BatchSurveyCompletionRates(location_type).get_completion_formatted_for_json(survey)
    json_dump = json.dumps(completion_rates, cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')

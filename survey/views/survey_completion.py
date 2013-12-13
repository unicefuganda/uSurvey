import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import Batch, Survey, Investigator
from survey.services.completion_rates_calculator import BatchLocationCompletionRates, BatchHighLevelLocationsCompletionRates, BatchSurveyCompletionRates
from survey.views.location_widget import LocationWidget
from survey.views.views_helper import contains_key


def is_valid(params):
    if contains_key(params, 'location') and contains_key(params, 'batch'):
        return True
    if params.has_key('location') and params['location'] == '' and contains_key(params, 'batch'):
        return True
    return False


def render_household_details(request, location, batch):
    context = {'selected_location': location, }
    investigator = Investigator.objects.filter(location=location)
    if not investigator.exists():
        messages.error(request, 'Investigator not registered for this location.')
        return render(request, 'aggregates/household_completion_status.html', context)

    completion_rates = BatchLocationCompletionRates(batch, location)
    context.update({'completion_rates': completion_rates, 'investigator': investigator[0],})
    return render(request, 'aggregates/household_completion_status.html', context)


def __get_parent_level_locations():
    country = LocationType.objects.filter(name__iexact='country')
    if country:
        return Location.objects.filter(tree_parent__type=country[0])

    return Location.objects.filter(tree_parent=None)


@login_required
@permission_required('auth.can_view_aggregates')
def show(request):
    selected_location = None
    params = request.GET
    content = {'selected_batch': None,
               'surveys': Survey.objects.all(),
               'batches': Batch.objects.all(),
               'action': 'survey_completion_rates',
               'request': request}

    if is_valid(params):
        batch = Batch.objects.get(id=params['batch'])
        location_id = params['location']
        high_level_locations = []

        if not location_id:
            high_level_locations = __get_parent_level_locations()
        else:
            selected_location = Location.objects.filter(id=location_id)
            if selected_location:
                selected_location = selected_location[0]
                high_level_locations = selected_location.get_children()
            if not high_level_locations:
                return render_household_details(request, selected_location, batch)

        content['completion_rates'] = BatchHighLevelLocationsCompletionRates(batch, high_level_locations)
        content['selected_batch'] = batch
        content['batches'] = content['batches'].filter(survey=batch.survey)

    elif params.has_key('location') or params.has_key('batch'):
        messages.error(request, "Please select a valid location and batch.")

    content['locations'] = LocationWidget(selected_location)

    return render(request, 'aggregates/completion_status.html', content)


def completion_json(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    location_type = LocationType.objects.get(name='District')
    completion_rates = BatchSurveyCompletionRates(location_type).get_completion_formatted_for_json(survey)
    json_dump = json.dumps(completion_rates, cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')
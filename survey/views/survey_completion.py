from django.contrib import messages
from django.shortcuts import render
from rapidsms.contrib.locations.models import Location
from survey.models import Batch, Survey, Household, Investigator
from survey.views.location_widget import LocationWidget
from survey.views.views_helper import contains_key


def _total_households(location):
    return Household.total_households_in(location)


def calculate_percent(numerator,denominator):
    try:
        return (numerator *100 / denominator)
    except ZeroDivisionError:
        return 0


def _percent_completed_households(location, batch):
    if batch:
        all_households = _total_households(location)
        completed_households = batch.completed_households.filter(household__in=all_households).count()
        return calculate_percent(completed_households, all_households.count())
    return None

def is_valid(params):
    if contains_key(params, 'location') and contains_key(params, 'batch'):
        return True
    if params.has_key('location') and params['location'] == '' and contains_key(params, 'batch'):
        return True
    return False


def render_household_details(request,location,batch):
    investigator = Investigator.objects.get(location=location)
    percent_completed = _percent_completed_households(location,batch)
    context = {'households': _total_households(location),'selected_location':location,'investigator':investigator,'percent_completed':percent_completed}
    return render(request, 'aggregates/household_completion_status.html', context)


def show(request):
    selected_location = None
    params = request.GET
    content = {'selected_batch': None}
    if is_valid(params):
        batch = Batch.objects.get(id=params['batch'])
        selected_location = Location.objects.get(id=params['location']) if params['location'] else None
        locations = selected_location.get_children() if selected_location else Location.objects.all()
        all_locations = locations if locations else None
        if all_locations is None:
            return render_household_details(request,selected_location,batch)
        content['total_households'] = {loc: _total_households(loc).count() for loc in all_locations}
        content['completed_households_percent'] = {loc: _percent_completed_households(loc, batch) for loc in
                                                   all_locations}
        content['selected_batch']= batch
    elif params.has_key('location') or params.has_key('batch'):
        messages.error(request, "Please select a valid location and batch.")


    content['surveys'] = Survey.objects.all()
    content['locations'] = LocationWidget(selected_location)
    content['batches'] = Batch.objects.all()
    content['action'] = 'survey_completion_rates'
    return render(request, 'aggregates/completion_status.html', content)

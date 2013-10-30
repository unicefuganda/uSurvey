from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import Batch, Survey, Household, Investigator, HouseholdBatchCompletion
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


def members_interviewed(household, batch):
    interviewed = household.members_interviewed(batch)
    if interviewed:
        return len(interviewed)
    return 0


def date_interviewed(household):
    for member in household.household_member.all():
        if not member.completed_member_batches.all().exists():
            return
    ordered_household_batch_completion = HouseholdBatchCompletion.objects.filter(household=household).order_by('created')
    if ordered_household_batch_completion.exists():
        return ordered_household_batch_completion[0].created.strftime('%d-%b-%Y %H:%M:%S')
    return


def render_household_details(request,location,batch):
    context={'selected_location':location,}
    investigator = Investigator.objects.filter(location=location)
    if not investigator.exists():
        messages.error(request, 'Investigator not registered for this location.')
        return render(request, 'aggregates/household_completion_status.html', context)
    percent_completed = _percent_completed_households(location,batch)
    all_households= _total_households(location)
    households = {household: members_interviewed(household,batch) for household in all_households}
    date_completed = {household: date_interviewed(household) for household in all_households}
    context.update({'households': households, 'investigator':investigator[0], 'percent_completed':percent_completed,'date_completed':date_completed})
    return render(request, 'aggregates/household_completion_status.html', context)

@login_required
@permission_required('auth.can_view_aggregates')
def show(request):
    selected_location = None
    params = request.GET
    content = {'selected_batch': None}
    if is_valid(params):
        batch = Batch.objects.get(id=params['batch'])
        selected_location = Location.objects.get(id=params['location']) if params['location'] else None
        tree_parent=None
        all_high_level_locations=Location.objects.filter(tree_parent=tree_parent)

        country = LocationType.objects.filter(name__iexact='country')

        if country.exists():
            tree_parent = Location.objects.filter(type=country[0])
            all_high_level_locations = Location.objects.filter(tree_parent__in=tree_parent)
        locations = selected_location.get_children() if selected_location else all_high_level_locations
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

from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

from rapidsms.contrib.locations.models import Location
from survey.models import HouseholdBatchCompletion
from survey.models.batch import Batch

from survey.views.location_widget import LocationWidget
from survey.views.views_helper import contains_key


def is_valid(params):
    if contains_key(params, 'location') and contains_key(params, 'batch'):
        return True
    if params.has_key('location')  and params['location'] == '':
        return True
    return False

@login_required
@permission_required('auth.can_view_aggregates')
def status(request):
    params = request.GET
    content = {'selected_batch': None}
    selected_location = None
    if is_valid(params):
        selected_location = Location.objects.get(id=params['location']) if params['location'] else None
        batch = Batch.objects.get(id=params['batch'])
        households_status, cluster_status, pending_investigators = HouseholdBatchCompletion.status_of_batch(batch, selected_location)
        content = { 'selected_location': selected_location,
                    'selected_batch': batch,
                    'households': households_status,
                    'clusters': cluster_status,
                    'investigators': pending_investigators,
                  }
    elif params.has_key('location') or params.has_key('batch'):
        messages.error(request, "Please select a valid location and batch.")

    content['locations'] = LocationWidget(selected_location)
    content['batches'] = Batch.objects.all()
    content['action'] = 'aggregates_status'
    return render(request, 'aggregates/status.html', content)
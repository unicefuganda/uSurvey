from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from survey.models import *

from rapidsms.contrib.locations.models import Location, LocationType
from survey.views.views_helper import initialize_location_type, update_location_type, get_posted_location

def status(request):
    params = request.GET
    content = {}
    if params.has_key('location') and  params.has_key('batch'):
        location = Location.objects.get(id=params['location'])
        batch = Batch.objects.get(id=params['batch'])
        households_status, cluster_status, pending_investigators = HouseholdBatchCompletion.status_of_batch(batch, location)
        content = { 'selected_location': location,
                    'selected_batch': batch,
                    'households': households_status,
                    'clusters': cluster_status,
                    'investigators': pending_investigators,
                  }
    return render(request, 'aggregates/status.html', content)
from django.shortcuts import render
from django.http import HttpResponse
from rapidsms.contrib.locations.models import Location, LocationType
from django.contrib.auth.decorators import login_required, permission_required
from survey.investigator_configs import *
from survey.models import Batch
from django.core.urlresolvers import reverse
from django.contrib import messages

@login_required
@permission_required('auth.can_view_batches')
def index(request):
    batches = Batch.objects.all()
    return render(request, 'batches/index.html', {'batches': batches, 'request': request})

@login_required
@permission_required('auth.can_view_batches')
def show(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    prime_location_type = LocationType.objects.get(name=PRIME_LOCATION_TYPE)
    locations = Location.objects.filter(type=prime_location_type).order_by('name')
    open_locations = Location.objects.filter(id__in = batch.open_locations.values_list('location_id', flat=True))
    return render(request, 'batches/show.html', {'batch': batch, 'locations': locations, 'open_locations': open_locations})

@login_required
@permission_required('auth.can_view_batches')
def open(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    location = Location.objects.get(id=request.POST['location_id'])
    batch.open_for_location(location)
    return HttpResponse()

@login_required
@permission_required('auth.can_view_batches')
def close(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    location = Location.objects.get(id=request.POST['location_id'])
    batch.close_for_location(location)
    return HttpResponse()
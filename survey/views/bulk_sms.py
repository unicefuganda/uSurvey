from django.shortcuts import render
from django.http import HttpResponseRedirect
from rapidsms.contrib.locations.models import Location, LocationType
from django.contrib.auth.decorators import login_required
from survey.investigator_configs import *
from survey.models import Investigator

@login_required
def view(request):
    location_type = LocationType.objects.get(name=SEND_BULK_SMS_TO_LOCATION_TYPE)
    locations = Location.objects.filter(type=location_type)
    return render(request, 'bulk_sms/index.html', {'locations': locations})

@login_required
def send(request):
    params = request.POST
    locations = Location.objects.filter(id__in=params['locations'])
    Investigator.sms_investigators_in_locations(locations=locations, text=params['text'])
    return HttpResponseRedirect("/bulk_sms/")
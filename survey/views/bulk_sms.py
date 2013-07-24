from django.shortcuts import render
from django.http import HttpResponse
from rapidsms.contrib.locations.models import Location, LocationType
from django.contrib.auth.decorators import login_required
from survey.investigator_configs import *

@login_required
def view(request):
    location_type = LocationType.objects.get(name=SEND_BULK_SMS_TO_LOCATION_TYPE)
    locations = Location.objects.filter(type=location_type)
    return render(request, 'bulk_sms/index.html', {'locations': locations})
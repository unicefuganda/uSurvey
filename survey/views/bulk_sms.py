from django.shortcuts import render
from django.http import HttpResponseRedirect
from survey.models import Location, LocationType
from django.contrib.auth.decorators import login_required, permission_required

from django.core.urlresolvers import reverse
from django.contrib import messages

from survey.models.interviewer import Interviewer


@login_required
@permission_required('auth.can_view_batches')
def view(request):
    location_type = LocationType.largest_unit()
    locations = Location.objects.filter(type=location_type).order_by('name')
    return render(request, 'bulk_sms/index.html', {'locations': locations})


@login_required
@permission_required('auth.can_view_batches')
def send(request):
    params = dict(request.POST)
    if valid_parameters(params, request):
        locations = Location.objects.filter(id__in=params['locations'])
        Interviewer.sms_interviewers_in_locations(
            locations=locations, text=params['text'][0])
        messages.success(
            request, "Your message has been sent to interviewers.")
    return HttpResponseRedirect(reverse('bulk_sms'))


def valid_parameters(params, request):
    if 'locations' not in params:
        messages.error(request, "Please select a location.")
        return False
    if len(params['text'][0]) < 1:
        messages.error(request, "Please enter the message to send.")
        return False
    return True

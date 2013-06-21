from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt

from survey.investigator_configs import *

from rapidsms.contrib.locations.models import *
from survey.models import Investigator
from survey.ussd import USSD


@csrf_exempt
def ussd(request):
    params = request.POST if request.method == 'POST' else request.GET
    mobile_number = params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
    try:
        investigator = Investigator.objects.get(mobile_number=mobile_number)
        response = USSD(investigator, params).response()
    except Investigator.DoesNotExist:
        response = USSD.investigator_not_registered_response()
    template = "ussd/%s.txt" % USSD_PROVIDER
    return render(request, template, response)

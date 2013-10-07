from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt

from survey.investigator_configs import *
from survey.models.investigator import Investigator
from survey.ussd.household_selection import HouseHoldSelection

from survey.views.ussd_base_view import USSDBaseView


@csrf_exempt
def ussd(request):
    params = request.POST if request.method == 'POST' else request.GET
    mobile_number = ""
    msisdn = params.get('msisdn', None)
    if msisdn:
        mobile_number = msisdn.replace(COUNTRY_PHONE_CODE, '')
    try:
        investigator = Investigator.objects.get(mobile_number=mobile_number)
        response = USSDBaseView(investigator, params).response()
    except Investigator.DoesNotExist:
        response = HouseHoldSelection(mobile_number, params).response()
    template = "ussd/%s.txt" % USSD_PROVIDER
    return render(request, template, response)

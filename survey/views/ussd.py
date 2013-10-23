from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt

from survey.investigator_configs import *
from survey.models import RandomHouseHoldSelection
from survey.models.investigator import Investigator
from survey.ussd.household_selection import HouseHoldSelection
from survey.ussd.ussd_survey import USSDSurvey

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
        random_household_selection = RandomHouseHoldSelection.objects.filter(mobile_number=mobile_number)
        if random_household_selection or investigator.households.all():
            response = USSDBaseView(investigator, params).response()
        else:
            response = HouseHoldSelection(mobile_number, params).response()
    except Investigator.DoesNotExist:
            response = USSDSurvey.investigator_not_registered_response()
    template = "ussd/%s.txt" % USSD_PROVIDER
    return render(request, template, response)

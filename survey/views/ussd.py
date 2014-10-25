from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from survey.investigator_configs import *
from survey.models.investigator import Investigator
from survey.ussd.ussd_pre_menu import USSDPremenu
from survey.ussd.ussd_survey import USSDSurvey


@csrf_exempt
def ussd(request):
    params = request.POST if request.method == 'POST' else request.GET
    msisdn = params.get('msisdn', '')
    mobile_number = msisdn.replace(COUNTRY_PHONE_CODE, '', 1)
    try:
        investigator = Investigator.objects.get(mobile_number=mobile_number)
        response = USSDPremenu(investigator, params).respond()
    except Investigator.DoesNotExist:
            response = USSDSurvey.investigator_not_registered_response()
    template = "ussd/%s.txt" % USSD_PROVIDER
    return render(request, template, response)

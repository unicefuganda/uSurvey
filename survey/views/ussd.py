from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from survey.interviewer_configs import *
from survey.models.interviewer import Interviewer
from survey.ussd.ussd_pre_menu import USSDPremenu
from survey.ussd.ussd_survey import USSDSurvey


@csrf_exempt
def ussd(request):
    params = request.POST if request.method == 'POST' else request.GET
    msisdn = params.get('msisdn', '')
    mobile_number = msisdn.replace(COUNTRY_PHONE_CODE, '', 1)
    try:
        interviewer = Interviewer.objects.get(mobile_number=mobile_number)
        response = USSDPremenu(interviewer, params).respond()
    except Interviewer.DoesNotExist:
        response = USSDSurvey.interviewer_not_registered_response()
    template = "ussd/%s.txt" % USSD_PROVIDER
    return render(request, template, response)

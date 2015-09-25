from django.core import serializers
from session_mgmt import manage
from django.http import  HttpResponse
from django.views.decorators.csrf import csrf_exempt
from survey.interviewer_configs import COUNTRY_PHONE_CODE


@csrf_exempt
def handle(request):
    if request.method == 'GET':
        data = request.GET
    else:
        data = request.POST
    trnx_id = data.get('transactionId', '').strip()
    msisdn = data.get('msisdn', '').strip()
    msisdn = msisdn[len(COUNTRY_PHONE_CODE):]
    request_string = data.get('ussdRequestString', '').strip()
    res = manage(msisdn, trnx_id, request_string)
    action = 0
    if res:
        action = 1
    ussd_resp = 'responseString=%s&action=%s' % (res, action)
    return HttpResponse(ussd_resp)
    

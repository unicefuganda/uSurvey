from django.core import serializers
from session_mgmt import manage
from django.http import  HttpResponse
from django.views.decorators.csrf import csrf_exempt
import phonenumbers
from django.conf import settings


@csrf_exempt
def handle(request):
    if request.method == 'GET':
        data = request.GET
    else:
        data = request.POST
    trnx_id = data.get('transactionId', '').strip()
    msisdn = data.get('msisdn', '').strip()
    try:
        pn = phonenumbers.parse(msisdn, settings.COUNTRY_CODE)
        if phonenumbers.is_valid_number_for_region(pn, settings.COUNTRY_CODE):
            msisdn = pn.national_number
        else:
            return HttpResponse('Invaid mobile number for your region')
    except phonenumbers.NumberParseException:
        return HttpResponse('Invaid mobile number')
    request_string = data.get('ussdRequestString', '').strip()
    res = manage(msisdn, trnx_id, request_string)
    action = 0
    if res:
        action = 1
    ussd_resp = 'responseString=%s&action=%s' % (res, action)
    return HttpResponse(ussd_resp)
    

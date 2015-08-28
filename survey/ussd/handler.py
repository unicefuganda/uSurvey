from django.core import serializers
from session_mgmt import manage
from django.http import  HttpResponse


def handle(request):
    if request.method == 'GET':
        data = request.GET
    else:
        data = request.POST
    trnx_id = data.get('transactionId')
    msisdn = data.get('msisdn')
    request_string = data.get('ussdRequestString')
    res = manage(msisdn, trnx_id, request_string)
    action = 0
    if res:
        action = 1
    ussd_resp = 'responseString=%s&action=%s' % (res, action)
    return HttpResponse(ussd_resp)
    

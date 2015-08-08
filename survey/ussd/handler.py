from django.core import serializers
from session_mgmt import interviewer_auth, manage


def handle(request):
    request = request.GET if request.method == 'GET' else request.POST
    trnx_id = request.get('transactionId')
    msisdn = request.get('msisdn')
    request_string = request.get('ussdRequestString')
    res = manage(msisdn, trnx_id, request_string)
    

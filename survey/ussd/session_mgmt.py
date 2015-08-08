from survey.models import USSDAccess
from django.core import serializers
from django.core.cache import cache

def interviewer_auth(func):
    @wraps(func)
    def _decorator(msisdn, *args, **kwargs):
        try:
            request = request.GET if request.method == 'GET' else request.POST
            trnx_id = request.get('transactionId')
            msisdn = request.get('msisdn')
            request_string = request.get('ussdRequestString')
            access = USSDAccess.objects.get(user_identifier=msisdn)
            kwargs['access_channel'] = access
            return func(access, *args, **kwargs)
        except USSDAccess.DoesNotExist:
            return HttpResponseNotAuthorized()
    return _decorator

@interviewer_auth
def manage(msisdn, trnx_id, request_string, access_channel=None):
    pass
#    interviewer =  

def get_method():
    pass
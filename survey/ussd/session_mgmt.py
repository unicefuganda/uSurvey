'''
    In the cache, paths as follows
    /interviewer/pk -- home
    /interviewer/pk/ongoing = {{task_name}} -- current ongoing task
    /interviewer/pk/locals  = List of local params-- current cached variables of on going task (shall mainly be used within interviewer tasks)

'''

from survey.models import USSDAccess
from django.core import serializers
from django.core.cache import cache
from functools import wraps
import flows

def ussd_login_required(func):
    @wraps(func)
    def _decorator(msisdn, *args, **kwargs):
        try:
#             request = request.GET if request.method == 'GET' else request.POST
#             trnx_id = request.get('transactionId')
#             msisdn = request.get('msisdn')
#             request_string = request.get('ussdRequestString')
            access = USSDAccess.objects.get(user_identifier=msisdn)
            kwargs['access'] = access
            return func(msisdn, *args, **kwargs)
        except USSDAccess.DoesNotExist:
            return flows.MESSAGES['USER_NOT_REGISTERED']
    return _decorator

@ussd_login_required
def manage(msisdn, trnx_id, request_string, access=None):
    ongoing_command_name = cache.get('/interviewer/%s/ongoing' % access.interviewer.pk, None)
    if ongoing_command_name is None:
        cache.set('/interviewer/%s/ongoing' % access.interviewer.pk, 'Start')
        return flows.Start(access.interviewer).intro()
    else:
        print ongoing_command_name
        ongoing_command = getattr(flows, ongoing_command_name)
        return ongoing_command(access.interviewer).respond(request_string)

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
from utils import reads_from_cache, refreshes_cache, saves_to_cache, ONGOING_COMMAND_NP
import flows

def ussd_login_required(func):
    @wraps(func)
    def _decorator(msisdn, *args, **kwargs):
        try:
#             request = request.GET if request.method == 'GET' else request.POST
#             trnx_id = request.get('transactionId')
#             msisdn = request.get('msisdn')
#             request_string = request.get('ussdRequestString')
            access = USSDAccess.objects.get(user_identifier=msisdn, is_active=True)
            kwargs['access'] = access
#            cache.set('/interviewer/%s/access' % access.interviewer.pk, access)
            return func(msisdn, *args, **kwargs)
        except USSDAccess.DoesNotExist:
            return flows.MESSAGES['USER_NOT_REGISTERED']
    return _decorator

class Mock(object):

    def __init__(self, access):
        self.access = access

    @property
    @reads_from_cache(store=ONGOING_COMMAND_NP)
    def ongoing_command(self):
        pass


@ussd_login_required
def manage(msisdn, trnx_id, request_string, access=None):
    ongoing_command_name = Mock(access).ongoing_command
    if ongoing_command_name is None:
        return flows.Start(access).intro()
    else:
        
        ongoing_command = getattr(flows, ongoing_command_name)
        return ongoing_command(access).respond(request_string)

from django.conf import settings
from django.core.cache import cache
# from survey.interviewer_configs import COUNTRY_PHONE_CODE


class CachedValue:

    def __getattr__(self, key):
        key = key.replace('__', '/')
        return cache.get(key)


def context_extras(request):
    generals = {'PROJECT_TITLE': settings.PROJECT_TITLE, 'country_phone_code': settings.COUNTRY_PHONE_CODE,
                'WEBSOCKET_URL': settings.WEBSOCKET_URL, 'WS_HEARTBEAT': settings.WS_HEARTBEAT,
                'cached_value': CachedValue()}
    if request.GET:
        generals['q'] = request.GET.get('q', '')
    return generals

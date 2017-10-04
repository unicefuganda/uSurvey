from django.conf import settings
import pycountry
from django.core.cache import cache


class CachedValue:

    def __getattr__(self, key):
        key = key.replace('__', '/')
        return cache.get(key)


def context_extras(request):
    generals = {
        'PROJECT_TITLE': settings.PROJECT_TITLE,
        'country_phone_code': pycountry.countries.lookup(settings.COUNTRY).alpha_2,
        'cached_value': CachedValue(),
        'max_display_per_page': settings.TABLE_ENTRY_PER_PAGINATION,
        'HOME_URL': request.build_absolute_uri('/')
    }
    if request.GET:
        generals['q'] = request.GET.get('q', '')
        generals['max_display_per_page'] = request.GET.get(
            'max_display_per_page', settings.TABLE_ENTRY_PER_PAGINATION)
    return generals

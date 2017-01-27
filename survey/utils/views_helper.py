from django.conf import settings
from cacheops import cache
from cacheops import CacheMiss
from django.utils import timezone


def contains_key(params, key):
    return params.has_key(key) and params[key].isdigit()


def is_not_digit_nor_empty(params, key):
    return key in params and not (params[key] == '' or params[key].isdigit())


def _get_descendants(location):
    children = location.get_children()
    if not children.exists():
        return [location]
    result = [location]
    for child in children:
        result.extend(_get_descendants(child))
    return result


def get_descendants(location, include_self=True):
    all_descendants_including_self = _get_descendants(location)
    if not include_self:
        all_descendants_including_self.remove(location)
    return all_descendants_including_self


def _get_ancestors(location):
    parent = location.tree_parent
    if not parent:
        return []
    result = [parent]
    result.extend(_get_ancestors(parent))
    return result


def get_ancestors(location, include_self=False):
    all_ancestors_including_self = _get_ancestors(location)
    if include_self:
        all_ancestors_including_self.insert(0, location)
    return all_ancestors_including_self


def clean_query_params(params):
    for key, value in params.items():
        if not value or str(value).lower() == 'all':
            del params[key]
    return params


def prepend_to_keys(params, text):
    new_params = {}
    for key, value in params.items():
        new_params[text + key] = value
    return new_params


def activate_super_powers(request):
    cache.set('%s:%s' % (request.user.pk, settings.SUPER_POWERS_KEY), data={'started': timezone.now()},
              timeout=settings.SUPER_POWERS_DURATION)


def deactivate_super_powers(request):
    try:
        return cache.delete('%s:%s' % (request.user.pk, settings.SUPER_POWERS_KEY))
    except:
        return 0


def has_super_powers(request):
    try:
        return cache.get('%s:%s' % (request.user.pk, settings.SUPER_POWERS_KEY))
    except CacheMiss:
        return False

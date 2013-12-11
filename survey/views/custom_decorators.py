from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from survey.models import BatchLocationStatus

try:
    from urllib.parse import urlparse
except ImportError:     # Python 2
    from urlparse import urlparse
from functools import wraps
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.decorators import available_attrs

def permission_required_for_perm_or_current_user(perm, login_url=None, raise_exception=False):
    def check_perms(user, user_id):
        # First check if the user has the permission or he's the user he wants to view himself
        if user.has_perm(perm) or str(user_id) == str(user.id):
            return True
        return False
    return custom_user_passes_test(check_perms, login_url=login_url)


def custom_user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            request_n_user_id = dict({'user':request.user}, **kwargs)
            if test_func(**request_n_user_id):
                return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def batch_passes_test(batch_is_open, message, redirect_url_name, url_kwargs_keys):
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if 'batch_id' in kwargs and batch_is_open(kwargs['batch_id']):
                messages.error(request, message)
                _kwargs ={_id: kwargs[_id] for _id in url_kwargs_keys}
                return HttpResponseRedirect(reverse(redirect_url_name, kwargs=_kwargs))
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def not_allowed_when_batch_is_open(message="This function is not allowed when batch is open.",
                                   redirect_url_name="login_page", url_kwargs_keys=None):
    def batch_is_open(batch_id):
        return BatchLocationStatus.objects.filter(batch=batch_id).exists()
    return batch_passes_test(batch_is_open, message, redirect_url_name, url_kwargs_keys)

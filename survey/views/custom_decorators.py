import urlparse
from functools import wraps

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.decorators import available_attrs

from survey.models import BatchLocationStatus


def permission_required_for_perm_or_current_user(perm, login_url=None):
    def check_perms(user, **kwargs):
        user_id = kwargs.get('user_id', '')
        if user.has_perm(perm) or str(user_id) == str(user.id):
            return True
        return False
    return _modified_django_auth_user_passes_test(check_perms, login_url=login_url)


def _modified_django_auth_user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user, **kwargs):  # changed to get kwargs as well
                return view_func(request, *args, **kwargs)
            messages.error(request, "Current user, %s, is not allowed to perform this action. "
                                    "Please log in a user with enough privileges." % request.user.get_full_name())
            path = request.build_absolute_uri()
            login_scheme, login_netloc = urlparse.urlparse(login_url or
                                                           settings.LOGIN_URL)[:2]
            current_scheme, current_netloc = urlparse.urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(path, login_url, redirect_field_name)
        return _wrapped_view
    return decorator


def batch_passes_test(batch_is_open, message, redirect_url_name, url_kwargs_keys):
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if 'batch_id' in kwargs and batch_is_open(kwargs['batch_id']):
                messages.error(request, message)
                _kwargs = {_id: kwargs[_id] for _id in url_kwargs_keys}
                return HttpResponseRedirect(reverse(redirect_url_name, kwargs=_kwargs))
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def not_allowed_when_batch_is_open(message="This function is not allowed when batch is open.",
                                   redirect_url_name="login_page", url_kwargs_keys=None):
    def batch_is_open(batch_id):
        return BatchLocationStatus.objects.filter(batch=batch_id).exists()
    return batch_passes_test(batch_is_open, message, redirect_url_name, url_kwargs_keys)


def handle_object_does_not_exist(message):
    def decorator(method):
        @wraps(method, assigned=available_attrs(method))
        def wrap(request, *args, **kwargs):
            from django.core.exceptions import ObjectDoesNotExist
            try:
                return method(request, *args, **kwargs)
            except ObjectDoesNotExist, ex:
                messages.error(request, message)
                return HttpResponseRedirect('/object_does_not_exist/')
        return wrap
    return decorator

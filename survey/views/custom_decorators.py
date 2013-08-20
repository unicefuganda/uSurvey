try:
    from urllib.parse import urlparse
except ImportError:     # Python 2
    from urlparse import urlparse
from functools import wraps
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.utils.decorators import available_attrs
from django.utils.encoding import force_str
from django.shortcuts import resolve_url


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
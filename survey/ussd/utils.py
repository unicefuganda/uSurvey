__author__ = 'anthony'
from functools import wraps
from django.core.cache import cache

LOCALS_NP = 'locals'
GLOBALS_NP = 'globals'
ONGOING_COMMAND_NP = 'ongoing'

def reads_from_cache(store=LOCALS_NP):
    def wrapper(func):
        @wraps(func)
        def _decorator(task):
            access = task.access
            result = cache.get('/interviewer/%s/%s/%s' % (access.interviewer.pk, store, func.__name__), None)
            if result is None:
                result = func(task)
                cache.set('/interviewer/%s/%s/%s' % (access.interviewer.pk, store, func.__name__), result)
            return result
        return _decorator
    return wrapper

def saves_to_cache(store=LOCALS_NP):
    def wrapper(func):
        @wraps(func)
        def _decorator(task, val):
            access = task.access
            result = func(task, val)
            if result:
                val = result
            cache.set('/interviewer/%s/%s/%s' % (access.interviewer.pk, store, func.__name__), val)
            return result
        return _decorator
    return wrapper

def refreshes_cache(store=LOCALS_NP, nps=None):
    def wrapper(func):
        @wraps(func)
        def _decorator(task, *args, **kwargs):
            access = task.access
            if nps is None:
                cache.delete_pattern('/interviewer/%s/%s*'%(access.interviewer.pk, store))
                print 'refreshed cache for ', args, ' store: ', store
            else:
                for np in nps:
                    cache.delete_pattern('/interviewer/%s/%s/%s'%(access.interviewer.pk, store, np))
                    print 'refreshed cache for ', args, ' store: ', store, 'pattern: ', np
            result = func(task, *args, **kwargs)
            return result
        return _decorator
    return wrapper


#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
from django.core.cache import cache
from django.conf import settings


PATH_FORMAT = '%(np)s/%(interviewer_id)s/%(key)s'


def get_entry(interviewer, key, default=None):
    return cache.get(PATH_FORMAT % {'np': settings.INTERVIEWER_SESSION_NAMESPACE,
                                    'interviewer_id': interviewer.pk,
                                    'key': key}, default)


def set_entry(interviewer, key, value):
    return cache.set(PATH_FORMAT % {'np': settings.INTERVIEWER_SESSION_NAMESPACE,
                                    'interviewer_id': interviewer.pk,
                                    'key': key}, value, timeout=settings.ONLINE_SURVEY_TIME_OUT)


def delete_entry(interviewer):
    CANCEL_PATH = '%(np)s/%(interviewer_id)s/' % {'np': settings.INTERVIEWER_SESSION_NAMESPACE,
                                                'interviewer_id': interviewer.pk,}
    cache.delete_pattern('%s*' % CANCEL_PATH)
#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
from django.conf import settings
from survey.utils.query_helper import to_df


def get_model_as_dump(model_class, **query_crtiteria):
    # following numenclacure header definition \
        #for model class to be call by
    # modelclass_EXPORT_HEADERS in settings all caps
    report_details = getattr(settings, '%s_EXPORT_HEADERS' % model_class.__name__.upper())
    keys = report_details.keys()
    if query_crtiteria:
        queryset = model_class.objects.filter(**query_crtiteria).values_list(*keys).order_by('id')
    else:
        queryset = model_class.objects.all().values_list(*keys).order_by('id')
    return to_df(queryset)

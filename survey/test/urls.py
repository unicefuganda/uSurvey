from django.conf.urls import patterns, include, url
from django.contrib.auth.models import User, AnonymousUser

urlpatterns = patterns('',
    url(r'^odk/collect/forms$', 'survey.test.views.form_list', name='odk_survey_forms_list'),
    url(r'^odk/collect/download/forms$', 'survey.test.views.download_xform', name='download_odk_survey_form'),
    )
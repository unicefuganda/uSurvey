from django.conf.urls import patterns, include, url
from survey.views import *
urlpatterns = patterns('',
    (r'^investigators/new', new_investigator),
    (r'^investigators$', create_or_list_investigators),
    (r'^investigators/locations', get_locations),
)

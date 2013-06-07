from django.conf.urls import patterns, include, url
from survey.views import *
urlpatterns = patterns('',
    url(r'^investigators/$', create_or_list_investigators, name="investigators_page"),
    url(r'^investigators/new', new_investigator, name="new_investigator_page"),
    url(r'^investigators/locations', get_locations, name="locations_autocomplete"),
    url(r'^investigators/check_mobile_number', check_mobile_number, name="check_mobile_number"),
    url(r'^ussd', ussd, name="ussd"),
)

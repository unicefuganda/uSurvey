from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from survey.views.investigator import *
from survey.views.ussd import *
from survey.views.household import *

urlpatterns = patterns('',
    url(r'^investigators/$', list_investigators, name="investigators_page"),
    url(r'^investigators/filter/(?P<location_id>\d+)/$', filter_list_investigators),
    url(r'^investigators/filter/$', list_investigators),
    url(r'^investigators/new/$', new_investigator, name="new_investigator_page"),
    url(r'^investigators/locations', get_locations, name="locations_autocomplete"),
    url(r'^investigators/check_mobile_number', check_mobile_number, name="check_mobile_number"),
    url(r'^ussd/simulator', TemplateView.as_view(template_name="ussd/simulator.html")),
    url(r'^ussd', ussd, name="ussd"),
    url(r'^households/new/$', new, name="new_household_page"),
    url(r'^households/investigators', get_investigators, name='load_investigators'),
)

from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'^$', 'survey.views.home_page.home', name='home_page'),
    url(r'^about/$', 'survey.views.home_page.about', name='about_page'),
    url(r'^investigators/$', 'survey.views.investigator.list_investigators', name="investigators_page"),
    url(r'^investigators/new/$', 'survey.views.investigator.new_investigator', name="new_investigator_page"),
    url(r'^investigators/locations', 'survey.views.investigator.get_locations', name="locations_autocomplete"),
    url(r'^investigators/check_mobile_number', 'survey.views.investigator.check_mobile_number', name="check_mobile_number"),
    url(r'^ussd/simulator', TemplateView.as_view(template_name="ussd/simulator.html")),
    url(r'^ussd', 'survey.views.ussd.ussd', name="ussd"),
    url(r'^households/new/$', 'survey.views.household.new', name="new_household_page"),
    url(r'^households/investigators', 'survey.views.household.get_investigators', name='load_investigators'),
    url(r'^aggregates/status', 'survey.views.aggregates.status', name='aggregates_status'),
    url(r'^location/(?P<location_id>\d+)/children', 'survey.views.location.children', name='get_location_children'),
    url(r'^aggregates/spreadsheet_report', 'survey.views.excel.download', name='excel_report'),
    url(r'^aggregates/download_spreadsheet', 'survey.views.excel.list', name='download_excel'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'accounts/login.html'}, name='login_page'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name='logout_page'),
)










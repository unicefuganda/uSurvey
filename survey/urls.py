from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.conf import settings

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
    url(r'^bulk_sms$', 'survey.views.bulk_sms.view', name='bulk_sms'),
    url(r'^bulk_sms/send$', 'survey.views.bulk_sms.send', name='send_bulk_sms'),
    url(r'^users/new/$', 'survey.views.users.new', name='new_user_page'),
    url(r'^users/', 'survey.views.users.index', name='users_index'),
    url(r'^batches/$', 'survey.views.batch.index', name='batch_index_page'),
    url(r'^batches/(?P<batch_id>\d+)/$', 'survey.views.batch.show', name='batch_show_page'),
    url(r'^batches/(?P<batch_id>\d+)/open_to$', 'survey.views.batch.open', name='batch_open_page'),
    url(r'^batches/(?P<batch_id>\d+)/close_to$', 'survey.views.batch.close', name='batch_close_page'),
)

if not settings.PRODUCTION:
    urlpatterns += (
        url(r'^api/create_investigator', 'survey.views.api.create_investigator', name='create_investigator'),
        url(r'^api/delete_investigator', 'survey.views.api.delete_investigator', name='delete_investigator'),
    )
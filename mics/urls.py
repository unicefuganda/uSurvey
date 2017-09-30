from django.conf.urls import include
from django.conf.urls import patterns
from django.contrib import admin
from survey.urls import urlpatterns as survey_urls
from django.conf import settings
from django.conf.urls import (handler400, handler403, handler404, handler500)

admin.autodiscover()

urlpatterns = patterns('',
                       (r'^admin/', include(admin.site.urls)),
                       (r'^admin/rq/', include('django_rq_dashboard.urls'))
                       ) + survey_urls

handler400 = 'survey.views.home_page.custom_400'
handler403 = 'survey.views.home_page.custom_403'
handler404 = 'survey.views.home_page.custom_404'
handler500 = 'survey.views.home_page.custom_500'


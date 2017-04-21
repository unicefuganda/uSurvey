from django.conf.urls import include
from django.conf.urls import patterns
from django.contrib import admin
from survey.urls import urlpatterns as survey_urls
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
                       (r'^admin/', include(admin.site.urls)),
                       (r'^admin/rq/', include('django_rq_dashboard.urls'))
                       ) + survey_urls

# Static content serving if not handled by web server
urlpatterns += patterns('',
                        (r'^static/(?P<path>.*)$',
                         'django.views.static.serve',
                         {'document_root': settings.STATIC_ROOT,
                          'show_indexes': False}),
                        (r'^media/(?P<path>.*)$',
                            'django.views.static.serve',
                            {'document_root': settings.MEDIA_ROOT,
                             'show_indexes': False}),
                        )

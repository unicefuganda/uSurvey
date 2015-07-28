from django.conf.urls import patterns, include, url
from django.contrib import admin
from survey.urls import urlpatterns as survey_urls
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    # Examples:
    # url(r'^$', 'mics.views.home', name='home'),
    # url(r'^mics/', include('mics.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
) + survey_urls


#Static content serving for development
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT, 'show_indexes': False}),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': False}),
        )
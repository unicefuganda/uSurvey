"""
WSGI config for mics project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mics.settings")
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from whitenoise import WhiteNoise

application = get_wsgi_application()
application = WhiteNoise(application, root=settings.STATIC_ROOT)


if settings.STATICFILES_DIRS:
    application.add_files(os.pathsep.join(settings.STATICFILES_DIRS))

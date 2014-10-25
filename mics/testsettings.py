from settings import *

DATABASES = {
   "default": {
       "ENGINE": "django.db.backends.postgresql_psycopg2",
       "NAME": "mics_test",
       "USER": "mnandri",
       "PASSWORD": "",
       "HOST": "localhost",
   }
}

INSTALLED_APPS = (
  'django.contrib.contenttypes',
  'django.contrib.auth',
  'django.contrib.sessions',
  'django.contrib.sites',
  'django.contrib.messages',
  'django.contrib.staticfiles',
  'django.contrib.admin',
  'django_nose',
  'south',
  'lettuce.django',
  'django_extensions',
  'rapidsms.contrib.locations',
  'rapidsms.contrib.locations.nested',
  'bootstrap_pagination',
  'survey',
  'celery',
   'djcelery',
  'rapidsms.backends.database',
  'rapidsms.contrib.httptester',
  # Uncomment the next line to enable the admin:
  # 'django.contrib.admin',
  # Uncomment the next line to enable admin documentation:
  # 'django.contrib.admindocs',
)


INSTALLED_BACKENDS = {
  "HTTP": {
      "ENGINE": "rapidsms.backends.database.DatabaseBackend",
  },
}

SOUTH_TESTS_MIGRATE = False

import logging
south_logger=logging.getLogger('south')
south_logger.setLevel(logging.INFO)
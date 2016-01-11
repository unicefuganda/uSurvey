# Django settings for mics project.
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

PROJECT_TITLE = 'uSurvey'
COUNTRY = 'UGANDA'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

CACHES = {
    'default': {
    'BACKEND': 'redis_cache.RedisCache',
    'LOCATION': [
    '127.0.0.1:6379',
    ],
    'OPTIONS': {
        'DB': 1,
        'PARSER_CLASS': 'redis.connection.HiredisParser',
        'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
        'CONNECTION_POOL_CLASS_KWARGS': {
        'max_connections': 50,
        'timeout': 5000,
    },
    'MAX_CONNECTIONS': 1000,
    'PICKLE_VERSION': -1,
    },
   },
}


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Africa/Kampala'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '6-bycz-+xpv@9+u8b^)#$-l&3cheum3i4cb_6$u6s%j6uu6s91'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "survey.context_processor.context_extras",
    "django.core.context_processors.request"
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'bootstrap_pagination.middleware.PaginationMiddleware',
    'breadcrumbs.middleware.BreadcrumbsMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'mics.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'mics.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'survey', 'templates'),
)

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
    'mptt',
    'rapidsms.backends.database',
    'rapidsms.contrib.httptester',
    'djcelery',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

SOUTH_MIGRATION_MODULES = {
        'djcelery': 'djcelery.south_migrations',
    }


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
'''
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

'''

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'


INSTALLED_BACKENDS = {
    # "HTTP": {
    #     "ENGINE": "rapidsms.backends.database.DatabaseBackend",
    # },
}

PRODUCTION = False

# cookies settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True

#email settings
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_EMAIL_SENDER = ''

#odk settings
TOKEN_DEFAULT_SIZE=5
ODK_DEFAULT_TOKEN='12345'
SUBMISSION_UPLOAD_BASE=os.path.join(BASE_DIR, 'submissions')
ANSWER_UPLOADS=os.path.join(BASE_DIR, 'answerFiles')
TEMP_DIR = os.path.join(BASE_DIR, 'tmp')
ODK_SUBMISSION_SUCCESS_MSG="Successful submission. Your submission is been Processed"
INTERVIEWER_EXPORT_HEADERS =  ['ea', 'name', 'age', 'level_of_education', 'language', 'mobile_numbers', 'odk_id']
from collections import OrderedDict
HOUSEHOLD_EXPORT_HEADERS =  OrderedDict([
                                    ('HOUSE NUMBER', 'house_number'),
                                    ('PHYSICAL ADDRESS', 'physical_address'),
                                    ('HEAD MEMBER',  'head_desc'),
                                    ('SEX' , 'head_sex'),
                                    ('ENUMERATION AREA', 'listing__ea__name')
                                    ])
AGGREGATORS = [('testAggregator', 'testAggregator'), ]
DEFAULT_AGGREGATOR = 'testAggregator'
TWITTER_URL = 'https://twitter.com/unicefuganda'
TWITTER_TOKEN = '617036281340657664'

###USSD config ##
USSD_NEXT = '*'
USSD_PREVIOUS = '#'
USSD_ITEMS_PER_PAGE = 10
USSD_RESTART = '##'
# USSD_STARTER = 'survey.ussd.flows.Start'
USSD_IGNORED_CHARACTERS = "*!#';&"
MAX_DISPLAY_PER_PAGE = 50
DEFAULT_TOTAL_HOUSEHOLDS_IN_EA = 1000
DATE_FORMAT = "%d-%m-%Y"
MOBILE_NUM_MIN_LENGTH = 9
MOBILE_NUM_MAX_LENGTH = 9
SHAPE_FILE_URI = '/static/map_resources/uganda_districts_2011_005.json'
SHAPE_FILE_LOC_FIELD ='DNAME_2010'
SHAPE_FILE_LOC_ALT_FIELD = 'DNAME_2006'

##end USSD config ##
# Importing server specific settings
try:
    from localsettings import *
except ImportError:
    pass

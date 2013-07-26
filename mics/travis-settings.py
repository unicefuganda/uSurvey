DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "mics",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_pylibmc.memcached.PyLibMCCache',
        'LOCATION': 'localhost:11211',
        'TIMEOUT': 500,
        'BINARY': False,
        'OPTIONS': {  # Maps to pylibmc "behaviors"
            'tcp_nodelay': True,
            'ketama': True
        }
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
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
    'rapidsms.backends.database',
    'rapidsms.contrib.httptester',
)

INSTALLED_BACKENDS = {
    "HTTP": {
        "ENGINE": "rapidsms.backends.database.DatabaseBackend",
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "app_test",
        "USER": "go",
        "PASSWORD": "go",
        "HOST": "localhost",
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_pylibmc.memcached.PyLibMCCache',
        'LOCATION': 'localhost:11211',
        'TIMEOUT': 3,
        'BINARY': False,
        'OPTIONS': {  # Maps to pylibmc "behaviors"
            'tcp_nodelay': True,
            'ketama': True
        }
    }
}

INSTALLED_BACKENDS = {
  "HTTP": {
      "ENGINE": "rapidsms.backends.database.DatabaseBackend",
  },
}

LETTUCE_AVOID_APPS = (
        'django_nose',
        'south',
        'django_extensions',
        'rapidsms.contrib.locations',
        'rapidsms.contrib.locations.nested',
        'bootstrap_pagination',
        'rapidsms.backends.database',
        'rapidsms.contrib.httptester',
        'djcelery',
)

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

INSTALLED_BACKENDS = {
    "HTTP": {
        "ENGINE": "rapidsms.contrib.httptester.backend.HttpTesterCacheBackend",
    },
}

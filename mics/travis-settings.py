DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "mics_test",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
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

import sys, os
#from djanfo.conf import settings
#settings.configure()
#export DJANGO_SETTINGS_MODULE="settings"
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
## Broker settings.
BROKER_URL = "amqp://guest:guest@localhost:5672//"

CELERY_RESULT_BACKEND = "amqp"

# List of modules to import when celery starts.
CELERY_IMPORTS = ("survey.tasks", )

if ('test' in sys.argv) or ('harvest' in sys.argv):
    CELERY_ALWAYS_EAGER = True

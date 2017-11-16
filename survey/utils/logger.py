__author__ = 'anthony'
import os
import logging
from django.conf import settings
from logging import handlers

LOG_ROTATE = 'midnight'
BASE_DIR = settings.LOG_DIR
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(message)s')
log_level = logging.DEBUG if settings.DEBUG else logging.INFO

# MODEL LOGGER
LOG_FILE = os.path.join(BASE_DIR, 'model.log')
mhandler = handlers.TimedRotatingFileHandler(LOG_FILE, when=LOG_ROTATE)
mhandler.setFormatter(formatter)
mlogger = logging.getLogger("usurvey_model")
mlogger.addHandler(mhandler)
mlogger.setLevel(log_level)

# MENU SESSION LOGGER
LOG_FILE = os.path.join(BASE_DIR, 'menusession.log')
shandler = handlers.TimedRotatingFileHandler(LOG_FILE, when=LOG_ROTATE)
shandler.setFormatter(formatter)
slogger = logging.getLogger("usurvey_menusession")
slogger.addHandler(shandler)
slogger.setLevel(log_level)

# GENERAL LOGGER
LOG_FILE = os.path.join(BASE_DIR, 'general.log')
ghandler = handlers.TimedRotatingFileHandler(LOG_FILE, when=LOG_ROTATE)
ghandler.setFormatter(formatter)
glogger = logging.getLogger("usurvey_general")
glogger.addHandler(ghandler)
glogger.setLevel(log_level)

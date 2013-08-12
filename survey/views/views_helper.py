from rapidsms.contrib.locations.models import *


def contains_key(params, key):
    return params.has_key(key) and params[key].isdigit()
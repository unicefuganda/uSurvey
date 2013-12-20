from rapidsms.contrib.locations.models import *


def contains_key(params, key):
    return params.has_key(key) and params[key].isdigit()


def is_not_digit_nor_empty(params, key):
    return key in params and not (params[key] == '' or params[key].isdigit())
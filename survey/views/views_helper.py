
def contains_key(params, key):
    return params.has_key(key) and params[key].isdigit()


def is_not_digit_nor_empty(params, key):
    return key in params and not (params[key] == '' or params[key].isdigit())


def _get_descendants(location):
    children = location.get_children()
    if not children.exists():
        return [location]
    result = [location]
    for child in children:
        result.extend(_get_descendants(child))
    return result


def get_descendants(location, include_self=True):
    all_descendants_including_self = _get_descendants(location)
    if not include_self:
        all_descendants_including_self.remove(location)
    return all_descendants_including_self
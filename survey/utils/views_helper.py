
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


def get_ancestors(location):
    parent = location.tree_parent
    if not parent:
        return []
    result = [parent]
    result.extend(get_ancestors(parent))
    return result


def clean_query_params(params):
    for key, value in params.items():
        if not value or str(value).lower() == 'all':
            del params[key]
    return params


def prepend_to_keys(params, text):
    new_params = {}
    for key, value in params.items():
        new_params[text+key] = value
    return new_params

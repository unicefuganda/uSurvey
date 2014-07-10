
def contains_key(params, key):
    return params.has_key(key) and params[key].isdigit()


def is_not_digit_nor_empty(params, key):
    return key in params and not (params[key] == '' or params[key].isdigit())

def get_descendants(location):
    children = location.get_children()
    if not children.exists():
        return [location]
    result = [location]
    for child in children:
        result.extend(get_descendants(child))
    return result

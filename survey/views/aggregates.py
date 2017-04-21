from survey.utils.views_helper import contains_key


def is_valid(params):
    if contains_key(params, 'location') and contains_key(params, 'batch'):
        return True
    if 'location' in params and params['location'] == '':
        return True
    return False

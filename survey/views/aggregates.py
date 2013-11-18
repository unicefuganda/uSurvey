from survey.views.views_helper import contains_key


def is_valid(params):
    if contains_key(params, 'location') and contains_key(params, 'batch'):
        return True
    if params.has_key('location')  and params['location'] == '':
        return True
    return False

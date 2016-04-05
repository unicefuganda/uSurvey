from django.conf import settings
# from survey.interviewer_configs import COUNTRY_PHONE_CODE

def context_extras (request):
    generals = { 'PROJECT_TITLE': settings.PROJECT_TITLE, 'country_phone_code' : settings.COUNTRY_CODE }
    if request.GET:
        generals['q'] = request.GET.get('q', '')
    return generals

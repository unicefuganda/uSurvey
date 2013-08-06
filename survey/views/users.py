import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages

from survey.investigator_configs import *
from survey.forms.users import *
from django.contrib.auth.decorators import login_required, permission_required

def _add_error_messages(userform, request):
    error_message = "User not registered. "
    messages.error(request, error_message + "See errors below.")

def _process_form(userform, request):
    if userform.is_valid():
        userform.save()
        messages.success(request, "User successfully registered.")
        return HttpResponseRedirect("/users/new/")

    _add_error_messages(userform, request)
    return None

@login_required
@permission_required('auth.can_view_users')
def new(request):
    userform = UserForm()
    response = None
    if request.method == 'POST':
        userform = UserForm(request.POST)
        response = _process_form(userform, request)

    template_variables = {'userform': userform,
                          'country_phone_code':COUNTRY_PHONE_CODE,
                          'action': "/users/new/",
                          'id': "create-user-form",
                          'button_label': "Create User",
                          'loading_text': "Creating..."}
    return response or render(request, 'users/new.html', template_variables)


def check_mobile_number(mobile_number):
    response = UserProfile.objects.filter(mobile_number=mobile_number).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

def check_user_attribute(**kwargs):
    response = User.objects.filter(**kwargs).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

@login_required
def index(request):
    if request.GET.has_key('mobile_number'):
        return check_mobile_number(request.GET['mobile_number'])

    if request.GET.has_key('username'):
        return check_user_attribute(username=request.GET['username'])

    if request.GET.has_key('email'):
        return check_user_attribute(email=request.GET['email'])

    return HttpResponse(status=200)

import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required

from survey.investigator_configs import *
from survey.forms.users import *
from survey.models.users import UserProfile
from survey.views.custom_decorators import permission_required_for_perm_or_current_user


def _add_error_messages(userform, request):
    error_message = "User not registered. "
    messages.error(request, error_message + "See errors below.")


def _process_form(userform, request, action_success="registered", redirect_url="/users/new/"):
    if userform.is_valid():
        userform.save()
        messages.success(request, "User successfully %s." % action_success)
        return HttpResponseRedirect(redirect_url)
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
                          'button_label': "Create",
                          'loading_text': "Creating...",
                          'title' : 'New User'}
    return response or render(request, 'users/new.html', template_variables)


def check_mobile_number(mobile_number):
    response = UserProfile.objects.filter(mobile_number=mobile_number).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

def check_user_attribute(**kwargs):
    response = User.objects.filter(**kwargs).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

@permission_required('auth.can_view_users')
def index(request):
    if request.GET.has_key('mobile_number'):
        return check_mobile_number(request.GET['mobile_number'])

    if request.GET.has_key('username'):
        return check_user_attribute(username=request.GET['username'])

    if request.GET.has_key('email'):
        return check_user_attribute(email=request.GET['email'])
    return render(request, 'users/index.html', { 'users' : User.objects.all(),
                                                 'request': request})
                                                 
@permission_required_for_perm_or_current_user('auth.can_view_users')
def edit(request, user_id):
    user = User.objects.get(pk=user_id)
    initial={'mobile_number': UserProfile.objects.get(user=user).mobile_number}
    userform = EditUserForm(user= request.user, instance=user, initial=initial)
    response = None
    if request.method == 'POST':
        userform = EditUserForm(data=request.POST, user= request.user, instance=user, initial=initial)
        response = _process_form(userform, request, 'edited', '/users/'+ str(user_id)+'/edit/')
    context_variables = {'userform': userform,
                        'action' : '/users/'+str(user_id)+'/edit/',
                        'id': 'edit-user-form', 'button_label' : 'Save',
                        'loading_text' : 'Saving...',
                        'country_phone_code': COUNTRY_PHONE_CODE,
                        'title': 'Edit User'}
    return response or render(request, 'users/new.html', context_variables)

@permission_required('auth.can_view_users')
def show(request, user_id):
    user = User.objects.filter(id=user_id)
    if not user.exists():
        messages.error(request, "User not found.")
        return HttpResponseRedirect("/users/")
    return render(request, 'users/show.html', {'the_user': user[0], 'cancel_url': '/users/'})

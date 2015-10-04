import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from survey.interviewer_configs import *
from survey.forms.users import *
from survey.models.users import UserProfile
from survey.views.custom_decorators import permission_required_for_perm_or_current_user
from survey.utils.query_helper import get_filterset
from django.core.urlresolvers import reverse


def _add_error_messages(userform, request, action_str='registered'):
    error_message = "User not %s. "%action_str
    messages.error(request, error_message + "See errors below.")


def _process_form(userform, request, action_success="registered"):
    if userform.is_valid():
        userform.save()
        messages.success(request, "User successfully %s." % action_success)
        return HttpResponseRedirect(reverse('users_index'))
    _add_error_messages(userform, request, action_success)
    return None

@login_required
@permission_required('auth.can_view_users')
def new(request):
    userform = UserForm()
    response = None
    if request.method == 'POST':
        userform = UserForm(request.POST)
        response = _process_form(userform, request)
    request.breadcrumbs([
        ('User list', reverse('users_index')),
    ])
    template_variables = {'userform': userform,
                          'country_phone_code':COUNTRY_PHONE_CODE,
                          'action': reverse('new_user_page'),
                          'cancel_url' : reverse('users_index'),
                          'id': "create-user-form",
                          'class': "user-form",
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
        return check_user_attribute(
                                    username=request.GET['username'])
    if request.GET.has_key('email'):
        return check_user_attribute(email=request.GET['email'])
    userlist = User.objects.exclude(is_superuser=True).order_by('first_name')
    search_fields = ['first_name', 'last_name', 'groups__name']
    if request.GET.has_key('q'):
        userlist = get_filterset(userlist, request.GET['q'], search_fields)
        
    if request.GET.has_key('status'):
        userlist = userlist.filter(is_active=(True if request.GET['status'].lower() == 'active' else False))
    
    return render(request, 'users/index.html', { 'users' : userlist,
                                                 'request': request})
                                                 
@permission_required_for_perm_or_current_user('auth.can_view_users')
def edit(request, user_id):
    user = User.objects.get(pk=user_id)
    initial={'mobile_number': UserProfile.objects.get(user=user).mobile_number}
    userform = EditUserForm(user= request.user, instance=user, initial=initial)
    response = None
    if request.method == 'POST':
        userform = EditUserForm(data=request.POST, user= request.user, instance=user, initial=initial)
        response = _process_form(userform, request, 'edited')
    request.breadcrumbs([
        ('User list', reverse('users_index')),
    ])
    context_variables = {'userform': userform,
                        'action' : reverse('users_edit', args=(user_id, )),
                         'cancel_url' : reverse('users_index'),
                        'id': 'edit-user-form','class': 'user-form', 'button_label' : 'Save',
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

def _set_is_active(user, status, request):
    action_str = "re-" if status else "de"
    user.is_active = status
    user.save()
    messages.success(request, "User %s successfully %sactivated."%(user.username, action_str))

def _activate(request, user_id, status):
    user = User.objects.filter(id=user_id)
    if not user.exists():
        messages.error(request, "User not found.")
        return HttpResponseRedirect("/users/")
    user = user[0]
    if user.is_active is not status:
        _set_is_active(user, status, request)
    return HttpResponseRedirect("/users/")

@permission_required('auth.can_view_users')
def deactivate(request, user_id):
    return _activate(request, user_id, status=False)

@permission_required('auth.can_view_users')
def activate(request, user_id):
    return _activate(request, user_id, status=True)

import json
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.conf import settings
from survey.interviewer_configs import *
from survey.forms.users import *
from survey.models.users import UserProfile
from survey.views.custom_decorators \
    import permission_required_for_perm_or_current_user
from survey.utils.query_helper import get_filterset
from survey.forms.filters import UsersFilterForm
from survey.services.export_model import get_model_as_dump
from django.shortcuts import get_list_or_404, get_object_or_404


def _add_error_messages(userform, request, action_str='registered'):
    error_message = "User not %s. " % action_str
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
                          'action': reverse('new_user_page'),
                          'cancel_url': reverse('users_index'),
                          'id': "create-user-form",
                          'class': "user-form",
                          'button_label': "Create",
                          'loading_text': "Creating...",
                          'title': 'New User'}
    return response or render(request, 'users/new.html', template_variables)


def check_mobile_number(mobile_number):
    response = UserProfile.objects.filter(mobile_number=mobile_number).exists()
    return HttpResponse(
        json.dumps(
            not response),
        content_type="application/json")


def check_user_attribute(**kwargs):
    response = User.objects.filter(**kwargs).exists()
    return HttpResponse(
        json.dumps(
            not response),
        content_type="application/json")


@login_required
@permission_required('auth.can_view_users')
def index(request):
    users_filter_form = UsersFilterForm(request.GET)
    userlist = users_filter_form.get_users()
    if 'mobile_number' in request.GET:
        return check_mobile_number(request.GET['mobile_number'])

    if 'username' in request.GET:
        return check_user_attribute(
            username=request.GET['username'])
    if 'email' in request.GET:
        return check_user_attribute(email=request.GET['email'])
    search_fields = ['first_name', 'last_name', 'groups__name']
    if 'q' in request.GET:
        userlist = get_filterset(userlist, request.GET['q'], search_fields)
    return render(request,
                  'users/index.html',
                  {'users': userlist,
                   'request': request,
                   'users_filter_form': users_filter_form})


@login_required
@permission_required_for_perm_or_current_user('auth.can_view_users')
def edit(request, user_id, mode=''):
    user = get_object_or_404(User, pk=user_id)
    initial = {'mobile_number': ''}
    try:
        mobile_number = UserProfile.objects.get(user=user).mobile_number
        initial = {'mobile_number': mobile_number}
    except UserProfile.DoesNotExist:
        pass
    userform = EditUserForm(user=request.user, instance=user, initial=initial)
    response = None
    if request.method == 'POST':
        userform = EditUserForm(
            data=request.POST,
            user=request.user,
            instance=user,
            initial=initial)
        response = _process_form(userform, request, 'edited')
    request.breadcrumbs([
        ('User list', reverse('users_index')),
    ])
    userform.fields['groups'].queryset = Group.objects.all().order_by('name')
    context_variables = {
        'userform': userform,
        'action': reverse(
            'users_edit',
            args=(
                user_id,
                mode)),
        'cancel_url': reverse('users_index'),
        'id': 'edit-user-form',
        'class': 'user-form',
            'button_label': 'Save',
            'loading_text': 'Saving...',
            'title': '%s User'% mode.title(),
            'mode': mode,
            'user_id': user.id}
    return response or render(request, 'users/new.html', context_variables)


@login_required
@permission_required('auth.can_view_users')
def show(request, user_id):
    user = User.objects.filter(id=user_id)
    if not user.exists():
        messages.error(request, "User not found.")
        return HttpResponseRedirect("/users/")
    return render(request, 'users/show.html',
                  {'the_user': user[0], 'cancel_url': '/users/'})


def _set_is_active(user, status, request):
    action_str = "re-" if status else "de"
    user.is_active = status
    user.save()
    messages.success(request, "User %s successfully %sactivated." %
                     (user.username, action_str))


def _activate(request, user_id, status):
    user = User.objects.filter(id=user_id)
    if not user.exists():
        messages.error(request, "User not found.")
        return HttpResponseRedirect("/users/")
    user = user[0]
    if user.is_active is not status:
        _set_is_active(user, status, request)
    return HttpResponseRedirect("/users/")


@login_required
@permission_required('auth.can_view_users')
def deactivate(request, user_id):
    return _activate(request, user_id, status=False)


@login_required
@permission_required('auth.can_view_users')
def activate(request, user_id):
    return _activate(request, user_id, status=True)


@login_required
@permission_required('auth.can_view_users')
def download_users(request):
    filename = 'all_admin_users'
    reports_df = get_model_as_dump(User)
    response = HttpResponse(content_type='text/csv')
    reports_df.to_csv(response, index=False)
    response['Content-Disposition'] = 'attachment; \
        filename="%s.csv"' % filename
    return response


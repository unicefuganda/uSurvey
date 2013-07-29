import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages

from survey.investigator_configs import *
from survey.forms.users import *
from django.contrib.auth.decorators import login_required

@login_required
def new(request):
    userform = UserForm()
    userprofile = UserProfileForm()
    template_variables = { 'userform': userform,
                           'user_profile_form':userprofile,
                          'action': "/accounts/new/",
                          'id': "create-user-form",
                          'button_label': "Create User",
                          'loading_text': "Creating..."}
    return render(request, 'accounts/new.html', template_variables)
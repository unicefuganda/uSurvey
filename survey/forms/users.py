from django import forms
from django.contrib.auth.models import User
from survey.models import UserProfile
from django.forms import ModelForm

class UserForm(ModelForm):

    class Meta:
        model = User
        exclude = ['date_joined', 'last_login']

class UserProfileForm(ModelForm):

    class Meta:
        model = UserProfile
        exclude =['user']


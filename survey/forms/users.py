from django import forms
from django.contrib.auth.models import User
from survey.models import UserProfile
from django.forms import ModelForm

class UserForm(ModelForm):

    mobile_number = forms.CharField( widget=forms.TextInput(attrs={'placeholder': 'Format: 771234567',
                                                                   'style':"width:172px;" ,
                                                                   'maxlength':'10',
                                                                   'type':'number'}))

    confirm_password = forms.CharField( widget=forms.PasswordInput(attrs={'placeholder':'ReType Password'}))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder= ['username', 'password', 'confirm_password', 'first_name', 'last_name',
                                'mobile_number', 'email', 'groups']

    class Meta:
        model = User
        exclude = ['date_joined', 'last_login', 'is_superuser', 'is_staff', 'user_permissions', 'is_active' ]

class UserProfileForm(ModelForm):

    class Meta:
        model = UserProfile
        exclude =['user']


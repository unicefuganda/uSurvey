from django import forms
from django.contrib.auth.models import User
from survey.models import UserProfile
from django.forms import ModelForm

class UserForm(ModelForm):

    mobile_number = forms.DecimalField(min_value=100000000,
                                       max_digits=9,
                                       widget=forms.TextInput(attrs={'placeholder': 'Format: 771234567',
                                                                   'style':"width:172px;" ,
                                                                   'maxlength':'10',
                                                                   'type':'number'}))

    confirm_password = forms.CharField( widget=forms.PasswordInput(attrs={'placeholder':'ReType Password'}))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder= ['username', 'password', 'confirm_password', 'first_name', 'last_name',
                                'mobile_number', 'email', 'groups']

    def save(self, commit = True, *args, **kwargs):
        user = super(UserForm, self).save(commit = commit, *args, **kwargs)
        if commit:
            user_profile = UserProfile.objects.create(user = user)
            user_profile.mobile_number = self.cleaned_data['mobile_number']
            user_profile.save()

        return user

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if not password or not confirm_password:
            return cleaned_data

        if password != confirm_password:
            message = "Password  mismatch."
            self._errors["confirm_password"] = self.error_class([message])
            del cleaned_data["confirm_password"]

        return cleaned_data

    class Meta:
        model = User
        exclude = ['date_joined', 'last_login', 'is_superuser', 'is_staff', 'user_permissions', 'is_active' ]
        widgets = {
            'password':forms.PasswordInput(attrs={'placeholder':'Type Password'})
        }

class UserProfileForm(ModelForm):

    class Meta:
        model = UserProfile
        exclude =['user']


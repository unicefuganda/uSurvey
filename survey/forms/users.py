from django import forms
from django.contrib.auth.models import User
from survey.models import UserProfile
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm

class UserForm(UserCreationForm):
    mobile_number = forms.DecimalField(min_value=100000000,
                                       max_digits=9,
                                       widget=forms.TextInput(attrs={'placeholder': 'Format: 771234567',
                                                                   'style':"width:172px;" ,
                                                                   'maxlength':'10'}))
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['password2'].label = 'Confirm Password'
        self.fields.keyOrder= ['username', 'password1', 'password2', 'first_name', 'last_name',
                                'mobile_number', 'email', 'groups']

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']
        users_with_the_same_mobile_number = UserProfile.objects.filter(mobile_number=mobile_number)
        if users_with_the_same_mobile_number.count()>0:
            message = "%s is already associated to a different user."% mobile_number
            self._errors['mobile_number'] = self.error_class([message])
            del self.cleaned_data['mobile_number']
        return mobile_number

    def clean_email(self):
        email = self.cleaned_data['email']
        users_with_the_same_email = User.objects.filter(email=email)
        if users_with_the_same_email.count()>0:
            message = "%s is already associated to a different user."% email
            self._errors['email'] = self.error_class([message])
            del self.cleaned_data['email']
        return email

    def save(self, commit = True, *args, **kwargs):
        user = super(UserForm, self).save(commit = commit, *args, **kwargs)
        if commit:
            self.save_m2m()
            user_profile = UserProfile.objects.create(user = user)
            user_profile.mobile_number = self.cleaned_data['mobile_number']
            user_profile.save()

        return user

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "groups")

class UserProfileForm(ModelForm):

    class Meta:
        model = UserProfile
        exclude =['user']


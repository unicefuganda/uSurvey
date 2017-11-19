from django import forms
from django.contrib.auth.models import User, Group
from django.forms import ModelForm
from django.conf import settings

from django.contrib.auth.forms import UserCreationForm

from survey.models.users import UserProfile


class UserForm(UserCreationForm):
    mobile_number = forms.CharField(
        max_length=settings.MOBILE_NUM_MAX_LENGTH,
        min_length=settings.MOBILE_NUM_MIN_LENGTH,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Format: 771234567',
                'style': "width:172px;",
                'maxlength': settings.MOBILE_NUM_MAX_LENGTH}))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['password2'].label = 'Confirm Password'
        self.fields.keyOrder = [
            'username',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'mobile_number',
            'email',
            'groups']
        self.fields['groups'].queryset = Group.objects.all().order_by('name')

    def clean_email(self):
        email = self.cleaned_data['email']
        users_with_email = User.objects.filter(email=email)
        if self.instance:
            users_with_email = users_with_email.exclude(pk=self.instance.pk)
        if users_with_email.exists():
            raise forms.ValidationError('This email already exist with: %s' %
                                        users_with_email.first().username)
        return email

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']
        users_with_mobile_number = UserProfile.objects.filter(mobile_number=mobile_number)
        if self.instance:
            users_with_mobile_number = users_with_mobile_number.exclude(user__pk=self.instance.pk)
        if users_with_mobile_number.exists():
            raise forms.ValidationError('This mobile_number already exist with: %s' %
                                        users_with_mobile_number.first().user.username)
        return mobile_number

    def save(self, commit=True, *args, **kwargs):
        user = super(UserForm, self).save(commit=commit, *args, **kwargs)
        if commit:
            self.save_m2m()
            mobile_number = self.cleaned_data['mobile_number']
            user_profile, b = UserProfile.objects.get_or_create(user=user, mobile_number=mobile_number)

        return user

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "groups")
        labels = {
            "groups": ("Roles"),
        }


class EditUserForm(ModelForm):
    mobile_number = forms.CharField(
        max_length=settings.MOBILE_NUM_MAX_LENGTH,
        min_length=settings.MOBILE_NUM_MIN_LENGTH,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Format: 771234567',
                'style': "width:172px;",
                'maxlength': settings.MOBILE_NUM_MAX_LENGTH}))
    password = forms.CharField(label="Password", required=False,
                               widget=forms.PasswordInput())

    confirm_password = forms.CharField(label="Confirm Password",
                                       required=False,
                                       widget=forms.PasswordInput())

    def __init__(self, user, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.set_form_fields_order(user)

    def set_form_fields_order(self, user):
        self.fields.keyOrder = ['username', 'first_name',
                                'last_name', 'mobile_number', 'email', ]
        if user.has_perm("auth.can_view_users"):
            self.fields.keyOrder.extend(
                ['password', 'confirm_password', 'groups'])

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']
        users_with_mobile_number = UserProfile.objects.filter(mobile_number=mobile_number)
        if self.instance:
            users_with_mobile_number = users_with_mobile_number.exclude(user__pk=self.instance.pk)
        if users_with_mobile_number.exists():
            raise forms.ValidationError('This mobile_number already exist with: %s' %
                                        users_with_mobile_number.first().user.username)
        return mobile_number

    def clean_email(self):
        email = self.cleaned_data['email']
        users_with_email = User.objects.filter(email=email)
        if self.instance:
            users_with_email = users_with_email.exclude(pk=self.instance.pk)
        if users_with_email.exists():
            raise forms.ValidationError('This email already exist with: %s' % users_with_email.first().username)
        return email

    def _clean_passwords(self, cleaned_data):
        password = cleaned_data.get('password', '')
        confirm_password = cleaned_data.get('confirm_password', '')
        if password != confirm_password:
            message = "passwords must match."
            self._errors['confirm_password'] = self.error_class([message])
            del cleaned_data['password']
            del cleaned_data['confirm_password']
        return password

    def clean(self):
        cleaned_data = super(EditUserForm, self).clean()
        self._clean_passwords(cleaned_data)
        return cleaned_data

    def save(self, commit=True, *args, **kwargs):
        user = super(EditUserForm, self).save(commit=commit, *args, **kwargs)
        self._change_password(user)
        if commit:
            self._create_or_update_profile(user)
            user.save()
        return user

    def _change_password(self, user):
        password = self.cleaned_data.get("password", None)
        if password:
            user.set_password(password)

    def _create_or_update_profile(self, user):
        mobile_number = self.cleaned_data['mobile_number']
        user_profile, b = UserProfile.objects.get_or_create(user=user, mobile_number=mobile_number)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "groups")
        widgets = {
            'username': forms.TextInput(attrs={'readonly': 'readonly'}),
        }
        labels = {
            "groups": "Roles",
        }


class UserProfileForm(ModelForm):

    class Meta:
        model = UserProfile
        exclude = ['user']

from django import forms
from django.contrib.auth.models import User, Group
from django.forms import ModelForm

from django.contrib.auth.forms import UserCreationForm

from survey.models.users import UserProfile


class UserForm(UserCreationForm):
    mobile_number = forms.DecimalField(
        min_value=100000000,
        max_digits=9,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Format: 771234567',
                'style': "width:172px;",
                'maxlength': '10'}))

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

    def _clean_attribute(self, Klass, **kwargs):
        attribute_name = kwargs.keys()[0]
        data_attr = kwargs[attribute_name]
        users_with_same_attr = Klass.objects.filter(**kwargs)
        if users_with_same_attr and self.initial.get(
                attribute_name, None) != str(data_attr):
            message = "%s is already associated to a different user." % data_attr
            self._errors[attribute_name] = self.error_class([message])
            del self.cleaned_data[attribute_name]
        return data_attr

    def clean_username(self):
        username = self.cleaned_data['username']
        return self._clean_attribute(User, username=username)

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']
        return self._clean_attribute(UserProfile, mobile_number=mobile_number)

    def clean_email(self):
        email = self.cleaned_data['email']
        return self._clean_attribute(User, email=email)

    def save(self, commit=True, *args, **kwargs):
        user = super(UserForm, self).save(commit=commit, *args, **kwargs)
        if commit:
            self.save_m2m()
            user_profile, b = UserProfile.objects.get_or_create(user=user)
            user_profile.mobile_number = self.cleaned_data['mobile_number']
            user_profile.save()

        return user

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "groups")


class EditUserForm(ModelForm):
    mobile_number = forms.DecimalField(
        min_value=100000000,
        max_digits=9,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Format: 771234567',
                'style': "width:172px;",
                'maxlength': '10'}))
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

    def _clean_attribute(self, Klass, **kwargs):
        attribute_name = kwargs.keys()[0]
        data_attr = kwargs[attribute_name]
        users_with_same_attr = Klass.objects.filter(**kwargs)
        if users_with_same_attr and self.initial.get(
                attribute_name, None) != str(data_attr):
            message = "%s is already associated to a different user." % data_attr
            self._errors[attribute_name] = self.error_class([message])
            del self.cleaned_data[attribute_name]
        return data_attr

    def clean_username(self):
        username = self.cleaned_data['username']
        users_with_same_username = User.objects.filter(username=username)
        if self.initial.get('username', None) != str(
                username) or not users_with_same_username:
            message = "username cannot be changed."
            self._errors['username'] = self.error_class([message])
            del self.cleaned_data['username']

        return username

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']
        return self._clean_attribute(UserProfile, mobile_number=mobile_number)

    def clean_email(self):
        email = self.cleaned_data['email']
        return self._clean_attribute(User, email=email)

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
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        user_profile.mobile_number = self.cleaned_data['mobile_number']
        user_profile.save()

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "groups")
        widgets = {
            'username': forms.TextInput(attrs={'readonly': 'readonly'}),
        }


class UserProfileForm(ModelForm):

    class Meta:
        model = UserProfile
        exclude = ['user']

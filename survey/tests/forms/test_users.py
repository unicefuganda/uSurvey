from django.test import TestCase
from survey.forms.users import *
from django.contrib.auth.models import User

class UserFormTest(TestCase):

    def setUp(self):
        self.form_data = {
        'username':'rajnii',
        'password':'kant',
        'confirm_password':'kant',
        'last_name':'Rajni',
        'email':'raj@ni.kant',
        }

    def test_valid(self):
        user_form = UserForm(self.form_data)
        user_form.is_valid()
        print user_form.errors
        self.assertTrue(user_form.is_valid())
        user = user_form.save()
        self.failUnless(user.id)
        user_retrieved = User.objects.get(last_name='Rajni')
        self.assertEqual(user_retrieved, user)

class UserProfileFormTest(TestCase):

    def setUp(self):
        self.form_data = {
        'mobile_number':'791234567',
        'permissions':'create user',
        }

    def test_valid(self):
        user_profile_form = UserProfileForm(self.form_data)
        self.assertTrue(user_profile_form.is_valid())
        user = User.objects.create(username='rajni', password='kant')
        user_profile_form.instance.user = user
        user_profile = user_profile_form.save()
        self.failUnless(user_profile.id)
        user_profile_retrieved = UserProfile.objects.get(user=user)
        self.assertEqual(user_profile_retrieved, user_profile)

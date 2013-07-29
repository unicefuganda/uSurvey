from django.test import TestCase
from survey.forms.users import *
from django.contrib.auth.models import User
from survey.models import *

class UserFormTest(TestCase):

    def setUp(self):
        self.form_data = {
        'username':'rajnii',
        'password':'kant',
        'confirm_password':'kant',
        'last_name':'Rajni',
        'email':'raj@ni.kant',
        'mobile_number':'791234567',
        }

    def test_valid(self):
        user_form = UserForm(self.form_data)
        self.assertTrue(user_form.is_valid())
        user = user_form.save()
        self.failUnless(user.id)
        user_retrieved = User.objects.get(last_name='Rajni')
        self.assertEqual(user_retrieved, user)

        user_profile = UserProfile.objects.filter(user=user)
        self.failUnless(user_profile)
        self.assertEquals(user_profile[0].mobile_number, self.form_data['mobile_number'])

    def test_NaN_mobile_number(self):
        form_data = self.form_data
        form_data['mobile_number']='not a number'
        user_form = UserForm(form_data)
        self.assertFalse(user_form.is_valid())
        message = "Enter a number."
        self.assertEquals(user_form.errors['mobile_number'], [message])

    def test_Negative_mobile_number(self):
        form_data = self.form_data
        form_data['mobile_number']=-123456789
        user_form = UserForm(form_data)
        self.assertFalse(user_form.is_valid())
        message = "Ensure this value is greater than or equal to 100000000."
        self.assertEquals(user_form.errors['mobile_number'], [message])

    def test_Negative_mobile_number(self):
        form_data = self.form_data
        number_of_length_greater_than_9 = 1234567890
        form_data['mobile_number']=number_of_length_greater_than_9
        user_form = UserForm(form_data)
        self.assertFalse(user_form.is_valid())
        message = "Ensure that there are no more than 9 digits in total."
        self.assertEquals(user_form.errors['mobile_number'], [message])

    def test_clean_confirm_password(self):
        form_data = self.form_data
        form_data['confirm_password'] = 'tank'
        user_form = UserForm(form_data)
        self.assertFalse(user_form.is_valid())
        message = "Password  mismatch."
        self.assertEquals(user_form.errors['confirm_password'], [message])

        form_data['confirm_password'] = form_data['password']
        user_form = UserForm(form_data)
        self.assertTrue(user_form.is_valid())

class UserProfileFormTest(TestCase):

    def setUp(self):
        self.form_data = {
        'mobile_number':'791234567',
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

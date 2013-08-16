from django.test import TestCase
from survey.forms.users import *
from django.contrib.auth.models import User, Group
from survey.models import *

class UserFormTest(TestCase):

    def setUp(self):
        self.form_data = {
        'username':'rajnii',
        'password1':'kant',
        'password2':'kant',
        'last_name':'Rajni',
        'email':'raj@ni.kant',
        'mobile_number':'791234567',
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

    def test_number_of_digits_in_mobile_number(self):
        form_data = self.form_data
        number_of_length_greater_than_9 = 1234567890
        form_data['mobile_number']=number_of_length_greater_than_9
        user_form = UserForm(form_data)
        self.assertFalse(user_form.is_valid())
        message = "Ensure that there are no more than 9 digits in total."
        self.assertEquals(user_form.errors['mobile_number'], [message])

    def test_email_already_used(self):
        form_data = self.form_data
        user = User.objects.create(email=form_data['email'])

        user_form = UserForm(form_data)
        self.assertFalse(user_form.is_valid())
        message = "%s is already associated to a different user."% form_data['email']
        self.assertEquals(user_form.errors['email'], [message])

    def test_clean_email_when_editing_a_user(self):
        form_data = self.form_data
        user = User.objects.create(username=form_data['username'], email=form_data['email'])

        user_form = UserForm(form_data, instance=user)
        self.assertTrue(user_form.is_valid())

    def test_mobile_number_already_used(self):
        form_data = self.form_data
        user = User.objects.create(username='some_other_name')
        userprofile = UserProfile.objects.create(user=user, mobile_number=form_data['mobile_number'])

        user_form = UserForm(form_data)
        self.assertFalse(user_form.is_valid())
        message = "%s is already associated to a different user."% form_data['mobile_number']
        self.assertEquals(user_form.errors['mobile_number'], [message])

    def test_clean_mobile_number_when_editing_a_user(self):
        form_data = self.form_data
        user = User.objects.create(username=form_data['username'])
        userprofile = UserProfile.objects.create(user=user, mobile_number=form_data['mobile_number'])

        user_form = UserForm(form_data, instance=user, initial={'mobile_number':form_data['mobile_number']})
        self.assertTrue(user_form.is_valid())

    def test_clean_username_no_duplicates_on_create(self):
        form_data = self.form_data
        user = User.objects.create(username=form_data['username'])
        user_form = UserForm(form_data)
        self.assertFalse(user_form.is_valid())
        message = "%s is already associated to a different user."% form_data['username']
        self.assertEquals(user_form.errors['username'], [message])

    def test_clean_user_name_when_editing_a_user(self):
        form_data = self.form_data
        user = User.objects.create(username=form_data['username'])

        user_form = UserForm(form_data, instance=user)
        self.assertTrue(user_form.is_valid())

    def test_clean_confirm_password(self):
        form_data = self.form_data
        form_data['password2'] = 'tank'
        user_form = UserForm(form_data)
        self.assertFalse(user_form.is_valid())
        message = "The two password fields didn't match."
        self.assertEquals(user_form.errors['password2'], [message])

        form_data['password2'] = form_data['password1']
        user_form = UserForm(form_data)
        self.assertTrue(user_form.is_valid())

class EditUserFormTest(TestCase):

    def setUp(self):
        self.user_data = {
        'username':'rajnii',
        'last_name':'Rajni',
        'email':'raj@ni.kant',
        }
        self.initial = {'mobile_number':'791234567'}
        self.user_to_be_edited = User.objects.create(**self.user_data)
        self.profile = UserProfile.objects.create(user=self.user_to_be_edited, mobile_number=self.initial['mobile_number'])

    def test_valid(self):
        user_data = self.user_data
        user_data['last_name'] = 'Rajniii'
        form_data = dict(user_data, **self.initial)
        user_form = EditUserForm(form_data, instance=self.user_to_be_edited, initial=self.initial)
        self.assertTrue(user_form.is_valid())
        user = user_form.save()
        self.failUnless(user.id)
        user_retrieved = User.objects.get(**user_data)
        self.assertEqual(user_retrieved, user)

        user_profile = UserProfile.objects.filter(user=user)
        self.failUnless(user_profile)
        self.assertEquals(user_profile[0].mobile_number, form_data['mobile_number'])

    def test_NaN_mobile_number(self):
        user_data = self.user_data
        form_data = dict(user_data, **{'mobile_number':'not a number'})

        user_form = EditUserForm(form_data, instance=self.user_to_be_edited, initial=self.initial)
        self.assertFalse(user_form.is_valid())
        message = "Enter a number."
        self.assertEquals(user_form.errors['mobile_number'], [message])

    def test_Negative_mobile_number(self):
        user_data = self.user_data
        form_data = dict(user_data, **{'mobile_number':-123456789})

        user_form = EditUserForm(form_data, instance=self.user_to_be_edited, initial=self.initial)
        self.assertFalse(user_form.is_valid())
        message = "Ensure this value is greater than or equal to 100000000."
        self.assertEquals(user_form.errors['mobile_number'], [message])

    def test_number_of_digits_in_mobile_number(self):
        number_of_length_greater_than_9 = 1234567890
        user_data = self.user_data
        form_data = dict(user_data, **{'mobile_number':number_of_length_greater_than_9})

        user_form = EditUserForm(form_data, instance=self.user_to_be_edited, initial=self.initial)
        self.assertFalse(user_form.is_valid())
        message = "Ensure that there are no more than 9 digits in total."
        self.assertEquals(user_form.errors['mobile_number'], [message])

    def test_email_already_used(self):
        user_data = self.user_data
        form_data = dict(user_data, **self.initial)
        some_email = 'haha@ha.ha'
        form_data['email'] = some_email

        other_user = User.objects.create(email=some_email)

        user_form = EditUserForm(form_data, instance=self.user_to_be_edited, initial=self.initial)
        self.assertFalse(user_form.is_valid())
        message = "%s is already associated to a different user."% form_data['email']
        self.assertEquals(user_form.errors['email'], [message])

    def test_mobile_number_already_used(self):
        user_data = self.user_data
        form_data = dict(user_data, **self.initial)
        some_number = '111111111'
        form_data['mobile_number'] = some_number

        other_user = User.objects.create(username='some_other_name')
        userprofile = UserProfile.objects.create(user=other_user, mobile_number=form_data['mobile_number'])

        user_form = EditUserForm(form_data, instance=self.user_to_be_edited, initial=self.initial)
        self.assertFalse(user_form.is_valid())
        message = "%s is already associated to a different user."% form_data['mobile_number']
        self.assertEquals(user_form.errors['mobile_number'], [message])

    def test_clean_username_should_not_work_if_user_does_not_exist_yet__this_form_is_for_editing_only(self):
        user_data = self.user_data
        form_data = dict(user_data, **self.initial)
        form_data['username']= 'some_non_existant_username'

        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)
        user_form = EditUserForm(form_data, instance=self.user_to_be_edited, initial=self.initial)
        self.assertFalse(user_form.is_valid())
        message = "username cannot be changed."
        self.assertEquals(user_form.errors['username'], [message])

    def test_clean_username_should_not_work_if_user_uses_other_existing_usernames_ie_no_changing_other_people_accounts(self):
        user_data = self.user_data
        form_data = dict(user_data, **self.initial)
        existing_username = 'some_other_existing_username'
        other_user,b = User.objects.get_or_create(username= existing_username)
        form_data['username']= existing_username

        user_form = EditUserForm(form_data, instance=self.user_to_be_edited, initial=self.initial)
        self.assertFalse(user_form.is_valid())
        message = "username cannot be changed."
        self.assertEquals(user_form.errors['username'], [message])

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

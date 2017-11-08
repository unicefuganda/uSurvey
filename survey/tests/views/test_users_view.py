import json
from django.test.client import Client
from django.core.urlresolvers import reverse
from mock import *
from django.contrib.auth.models import User, Group
from survey.models.users import UserProfile
from survey.tests.base_test import BaseTest
from survey.forms.users import UserForm, EditUserForm


class UsersViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.user_without_permission = User.objects.create_user(
            username='useless', email='demo13@kant.com', password='I_Suck')
        self.raj = self.assign_permission_to(User.objects.create_user(
            'demo13', 'demo13@kant.com', 'demo13'), 'can_view_users')
        self.client.login(username='demo13', password='demo13')

    def test_new(self):
        response = self.client.get(reverse('new_user_page'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('users/new.html', templates)
        self.assertEquals(response.context['action'], reverse('new_user_page'))
        self.assertEquals(response.context['id'], 'create-user-form')
        self.assertEquals(response.context['class'], 'user-form')
        self.assertEquals(response.context['button_label'], 'Create')
        self.assertEquals(response.context['loading_text'], 'Creating...')
        self.assertEquals(response.context['country_phone_code'], '+256')
        self.assertIsInstance(response.context['userform'], UserForm)
        self.assertEqual(response.context['title'], 'New User')

    @patch('django.contrib.messages.success')
    def test_create_users(self, success_message):
        some_group = Group.objects.create()
        form_data = {
            'username': 'knight',
            'password1': 'mk',
            'password2': 'mk',
            'first_name': 'michael',
            'last_name': 'knight',
            'mobile_number': '123456789',
            'email': 'mm@mm.mm',
            'groups': some_group.id,
        }
        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)
        response = self.client.post(reverse('new_user_page'), data=form_data)
        self.failUnlessEqual(response.status_code, 302)

        user = User.objects.get(username=form_data['username'])
        self.failUnless(user.id)
        for key in ['username', 'first_name', 'last_name', 'email']:
            value = getattr(user, key)
            self.assertEqual(form_data[key], str(value))

        user_groups = user.groups.all()
        self.assertEquals(len(user_groups), 1)
        self.assertIn(some_group, user_groups)

        user_profile = UserProfile.objects.filter(user=user)
        self.failUnless(user_profile)
        self.assertEquals(
            user_profile[0].mobile_number, form_data['mobile_number'])

        assert success_message.called

    def test_create_users_unsuccessful(self):
        some_group = Group.objects.create()
        form_data = {
            'username': 'knight',
            'password': 'mk',
            'confirm_password': 'mk',
            'first_name': 'michael',
            'last_name': 'knight',
            'mobile_number': '123456789',
            'email': 'mm@mm.mm',
            'groups': some_group.id,
        }
        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)

        form_data['confirm_password'] = 'hahahaha'

        response = self.client.post(reverse('new_user_page'), data=form_data)
        self.failUnlessEqual(response.status_code, 200)
        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)
        self.assertEqual(1, len(response.context['messages']._loaded_messages))
        self.assertIn("User not registered. See errors below.",
                      response.context['messages']._loaded_messages[0].message)

        form_data['confirm_password'] = form_data['password']
        unexisting_group_id = 123456677
        form_data['groups'] = unexisting_group_id

        response = self.client.post(reverse('new_user_page'), data=form_data)
        self.failUnlessEqual(response.status_code, 200)
        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)
        self.assertEqual(1, len(response.context['messages']._loaded_messages))
        self.assertIn("User not registered. See errors below.",
                      response.context['messages']._loaded_messages[0].message)

        form_data['groups'] = some_group.id
        user = User.objects.create(username='some_other_name')
        userprofile = UserProfile.objects.create(
            user=user, mobile_number=form_data['mobile_number'])

        response = self.client.post(reverse('new_user_page'), data=form_data)
        self.failUnlessEqual(response.status_code, 200)
        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)
        self.assertEqual(1, len(response.context['messages']._loaded_messages))
        self.assertIn("User not registered. See errors below.",
                      response.context['messages']._loaded_messages[0].message)

    def test_index(self):
        response = self.client.get(reverse('users_index'))
        self.failUnlessEqual(response.status_code, 200)

    def test_check_mobile_number(self):
        user = User.objects.create(username='some_other_name')
        userprofile = UserProfile.objects.create(
            user=user, mobile_number='123456789')
        url = '%s?mobile_number=987654321' % reverse('users_index')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)
        url = "%s?mobile_number=" % reverse('users_index')
        url = url+userprofile.mobile_number
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

    def test_check_username(self):
        user = User.objects.create(username='some_other_name')
        url = '%s?username=demo13' % reverse('users_index')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

        response = self.client.get(
            "%s?username=%s" %(reverse('users_index'),user.username))
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

    def test_check_email(self):
        user = User.objects.create(email='haha@ha.ha')
        self.client.login(username='demo13', password='I_suck')
        url = '%s?email=bla@bla.bl' % reverse('users_index')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)
        url = "%s?email=" % reverse('users_index') + user.email
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

    def test_list_users(self):
        user = User.objects.create()
        response = self.client.get(reverse('users_index'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('users/index.html', templates)
        self.assertEqual(len(response.context['users']), 3)
        self.assertIn(user, response.context['users'])
        self.assertNotEqual(None, response.context['request'])

    def test_edit_user_view(self):
        user = User.objects.create_user('andrew', 'a@m.vom', 'pass')
        UserProfile.objects.create(user=user, mobile_number='200202020')
        url = reverse(
            'users_edit',
            kwargs={"user_id":  str(user.pk), "mode":  "edit"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('users/new.html', templates)
        self.assertEquals(response.context['action'], url)
        self.assertEquals(response.context['id'], 'edit-user-form')
        self.assertEquals(response.context['class'], 'user-form')
        self.assertEquals(response.context['title'], 'Edit User')
        self.assertEquals(response.context['button_label'], 'Save')
        self.assertEquals(response.context['loading_text'], 'Saving...')
        self.assertEquals(response.context['country_phone_code'], '+256')
        self.assertIsInstance(response.context['userform'], EditUserForm)

    def test_edit_user_updates_user_information(self):
        form_data = {
            'username': 'knight',
            'password': 'mk',
            'confirm_password': 'mk',
            'first_name': 'michael',
            'last_name': 'knight',
            'mobile_number': '123456789',
            'email': 'mm@mm.mm',
        }
        self.failIf(User.objects.filter(username=form_data['username']))
        user = User.objects.create(
            username=form_data['username'],
            email=form_data['email'],
            password=form_data['password'])
        UserProfile.objects.create(
            user=user, mobile_number=form_data['mobile_number'])
        data = {
            'username': 'knight',
            'password': 'mk',
            'confirm_password': 'mk',
            'first_name': 'michael',
            'last_name': 'knightngale',
            'mobile_number': '123456789',
            'email': 'mm@mm.mm',
        }
        url = reverse(
            'users_edit',
            kwargs={"user_id":  str(user.pk), "mode":  "edit"})
        response = self.client.post(url, data=data)
        self.failUnlessEqual(response.status_code, 302)
        edited_user = User.objects.filter(last_name=data['last_name'])
        self.assertEqual(1, edited_user.count())
        self.assertTrue(edited_user[0].check_password(data['password']))

    def test_edit_username_not_allowed(self):
        form_data = {
            'username': 'knight',
            'password': 'mk',
            'confirm_password': 'mk',
            'first_name': 'michael',
            'last_name': 'knight',
            'mobile_number': '123456789',
            'email': 'mm@mm.mm',
        }
        self.failIf(User.objects.filter(username=form_data['username']))
        user = User.objects.create(
            username=form_data['username'],
            email=form_data['email'],
            password=form_data['password'])
        UserProfile.objects.create(
            user=user, mobile_number=form_data['mobile_number'])
        data = form_data.copy()
        data['username'] = 'changed'
        url = reverse(
            'users_edit',
            kwargs={"user_id":  str(user.pk), "mode":  "edit"})
        response = self.client.post(url, data=data)        
        self.assertIn(response.status_code, [302,200])
        edited_user = User.objects.filter(username=data['username'])
        #self.failIfUnless(edited_user)
        original_user = User.objects.filter(
            username=form_data['username'], email=form_data['email'])


    def test_current_user_edits_his_own_profile(self):
        form_data = {
            'username': 'knight',
            'password': 'mk',
            'confirm_password': 'mk',
            'first_name': 'michael',
            'last_name': 'knight',
            'mobile_number': '123456789',
            'email': 'mm@mm.mm',
        }
        self.failIf(User.objects.filter(username=form_data['username']))
        user_without_permission = User.objects.create(
            username=form_data['username'], email=form_data['email'])
        user_without_permission.set_password(form_data['password'])
        user_without_permission.save()
        UserProfile.objects.create(
            user=user_without_permission,
            mobile_number=form_data['mobile_number'])
        self.client.logout()
        self.client.login(
            username=form_data['username'],
            password=form_data['password'])
        data = {
            'username': 'knight',
            'first_name': 'michael',
            'password': 'changed mk',
            'confirm_password': 'changed mk',
            'last_name': 'knightngale',
            'mobile_number': '123456789',
            'email': 'mm@mm.mm',
        }
        url = reverse(
            'users_edit',
            kwargs={
                "user_id":  str(user_without_permission.pk),
                "mode":  "edit"})
        response = self.client.post(url, data=data)
        self.failUnlessEqual(response.status_code, 302)
        edited_user = User.objects.filter(last_name=data['last_name'])
        self.assertEqual(1, edited_user.count())
        self.assertFalse(edited_user[0].check_password(form_data['password']))
        self.assertTrue(edited_user[0].check_password(data['password']))

    def test_a_non_admin_user_cannot_POST_edit_other_users_profile(self):
        user_without_permission = User.objects.create_user(
            username='notpermitted', email='demo13@kant.com', password='I_Suck')
        self.client.logout()
        self.client.login(
            username=user_without_permission.username, password='I_Suck')
        data = {
            'username': 'knight',
            'first_name': 'michael',
            'last_name': 'knightngale',
            'mobile_number': '123456789',
            'email': 'mm@mm.mm',
        }
        original_demo13_attributes = User.objects.filter(
            username=self.raj).values()[0]
        edit_demo13_url = reverse(
            'users_edit',
            kwargs={"user_id":  str(self.raj.pk), "mode":  "edit"})
        response = self.client.post(edit_demo13_url, data=data)
        self.assertRedirects(
            response,
            expected_url="%s?next=%s" % (
                reverse('login_page'),
                edit_demo13_url))
        retrieved_demo13 = User.objects.filter(**original_demo13_attributes)
        self.assertEqual(1, retrieved_demo13.count())

    def test_a_non_admin_user_cannot_GET_edit_other_users_profile(self):
        user_without_permission = User.objects.create_user(
            username='notpermitted', email='demo13@kant.com', password='I_Suck')
        self.client.logout()
        self.client.login(
            username=user_without_permission.username, password='I_Suck')
        original_demo13_attributes = User.objects.filter(
            username=self.raj).values()[0]
        edit_demo13_url = reverse(
            'users_edit',
            kwargs={"user_id":  str(self.raj.pk), "mode":  "edit"})
        response = self.client.get(edit_demo13_url)
        self.assertRedirects(
            response, expected_url="%s?next=%s" % (
                reverse('login_page'),
                edit_demo13_url))
        retrieved_demo13 = User.objects.filter(**original_demo13_attributes)
        self.assertEqual(1, retrieved_demo13.count())

    def test_view_user_details(self):
        user = User.objects.create_user(
            username='rrdemo13',
            email='rdemo13@kant.com',
            password='demo13_0',
            first_name='some name',
            last_name='last_name')
        UserProfile.objects.create(user=user, mobile_number='123456666')
        url = reverse('users_edit', kwargs={"user_id":  user.id,'mode':'view'})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('users/new.html', templates)
        self.assertEquals(
            response.context['cancel_url'],
            reverse('users_index'))

    def test_view_user_details_when_no_such_user_exists(self):
        non_existing_user_id = 111
        url = reverse(
            'users_edit',
            kwargs={"user_id":  non_existing_user_id,"mode":"view"})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_deactivate_user(self):
        user = User.objects.create_user(
            username='rrdemo13',
            email='rdemo13@kant.com',
            password='demo13_0',
            first_name='some name',
            last_name='last_name')
        UserProfile.objects.create(user=user, mobile_number='123456666')
        response = self.client.get(
            reverse('deactivate_user', kwargs={"user_id":  user.id}))
        self.assertRedirects(response, expected_url=reverse('users_index'))
        self.assertIn("User %s successfully deactivated." %
                      user.username, response.cookies['messages'].value)

    def test_deactivate_user_when_no_such_user_exist(self):
        non_existing_user_id = 222
        url = reverse(
            'deactivate_user',
            kwargs={"user_id":  non_existing_user_id})
        response = self.client.get(url)
        self.assertRedirects(response, expected_url=reverse('users_index'))
        self.assertIn("User not found.", response.cookies['messages'].value)

    def test_reactivate_user(self):
        user = User.objects.create_user(
            username='rrdemo13',
            email='rdemo13@kant.com',
            password='demo13_0',
            first_name='some name',
            last_name='last_name')
        UserProfile.objects.create(user=user, mobile_number='123456666')
        user.is_active = False
        user.save()
        self.assertFalse(user.is_active)
        url = reverse('activate_user', kwargs={"user_id":  user.id})
        response = self.client.get(url)
        self.assertRedirects(response, expected_url=reverse('users_index'))
        self.assertIn("User %s successfully re-activated." %
                      user.username, response.cookies['messages'].value)

    def test_deactivate_user_when_no_such_user_exist(self):
        non_existing_user_id = 222
        url = reverse(
            'activate_user',
            kwargs={"user_id":  non_existing_user_id})
        response = self.client.get(url)
        self.assertRedirects(response, expected_url=reverse('users_index'))
        self.assertIn("User not found.", response.cookies['messages'].value)

    def test_restricted_permission(self):
        self.assert_restricted_permission_for(reverse('new_user_page'))
        self.assert_restricted_permission_for(reverse('users_index'))
        url = reverse('users_edit', kwargs={"user_id":  1, "mode": "view"})
        url = reverse('deactivate_user', kwargs={"user_id":  1})
        self.assert_restricted_permission_for(url)

    def test_download(self):
        some_group = Group.objects.create(name='abc')
        form_data = {
            'username': 'knight111',
            'password': 'mk',
            'first_name': 'demo',
            'last_name': 'knight',
            'mobile_number': '123456789',
            'email': 'mm@mm.mm',
            'groups': some_group.id,
        }
        user = User.objects.create(
            username=form_data['username'],
            email=form_data['email'],
            password=form_data['password'],
            first_name=form_data['first_name'],
            last_name=form_data['last_name'])
        UserProfile.objects.create(
            user=user, mobile_number=form_data['mobile_number'])
        filename = 'all_admin_users'
        url = reverse('download_users')
        url = url + "?first_name__in=demo"
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get('content-type'), 'text/csv')
        self.assertIn('%s'%form_data['first_name'], response.content)

        url = reverse('download_users')        
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get('content-type'), 'text/csv')
        self.assertIn('%s'%form_data['first_name'], response.content)

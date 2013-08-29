import json

from django.test import TestCase
from django.test.client import Client
from mock import *

from survey.models_file import *
from survey.forms.users import UserForm, EditUserForm
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType


class UsersViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user(username='Rajni', email='rajni@kant.com', password='I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_users', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)

        self.client.login(username='Rajni', password='I_Rock')

    def test_new(self):
        response = self.client.get('/users/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('users/new.html', templates)
        self.assertEquals(response.context['action'], '/users/new/')
        self.assertEquals(response.context['id'], 'create-user-form')
        self.assertEquals(response.context['button_label'], 'Create User')
        self.assertEquals(response.context['loading_text'], 'Creating...')
        self.assertEquals(response.context['country_phone_code'], '256')
        self.assertIsInstance(response.context['userform'], UserForm)
        self.assertEqual(response.context['title'], 'New User')

    @patch('django.contrib.messages.success')
    def test_create_users(self, success_message):
        some_group = Group.objects.create()
        form_data = {
                    'username':'knight',
                    'password1':'mk',
                    'password2':'mk',
                    'first_name':'michael',
                    'last_name':'knight',
                    'mobile_number':'123456789',
                    'email':'mm@mm.mm',
                    'groups':some_group.id,
                }

        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)
        response = self.client.post('/users/new/', data=form_data)
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
        self.assertEquals(user_profile[0].mobile_number, form_data['mobile_number'])

        assert success_message.called

    @patch('django.contrib.messages.error')
    def test_create_users_unsuccessful(self, error_message):
        some_group = Group.objects.create()
        form_data = {
                    'username':'knight',
                    'password':'mk',
                    'confirm_password':'mk',
                    'first_name':'michael',
                    'last_name':'knight',
                    'mobile_number':'123456789',
                    'email':'mm@mm.mm',
                    'groups':some_group.id,
                }

        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)

        form_data['confirm_password']='hahahaha'

        response = self.client.post('/users/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 200)
        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)
        assert  error_message.called

        error_message.reset_mock()
        form_data['confirm_password']= form_data['password']
        unexisting_group_id = 123456677
        form_data['groups'] = unexisting_group_id

        response = self.client.post('/users/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 200)
        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)
        assert error_message.called

        error_message.reset_mock()
        form_data['groups']= some_group.id
        user = User.objects.create(username='some_other_name')
        userprofile = UserProfile.objects.create(user=user, mobile_number=form_data['mobile_number'])

        response = self.client.post('/users/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 200)
        user = User.objects.filter(username=form_data['username'])
        self.failIf(user)
        assert error_message.called

    def assert_restricted_permission_for(self, url):
        self.client.logout()

        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)

        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%url, status_code=302, target_status_code=200, msg_prefix='')

    def test_restricted_permission(self):
        self.assert_restricted_permission_for('/users/new/')
        self.assert_restricted_permission_for('/users/')


    def test_index(self):
        response = self.client.get('/users/')
        self.failUnlessEqual(response.status_code, 200)

    def test_check_mobile_number(self):
        user = User.objects.create(username='some_other_name')
        userprofile = UserProfile.objects.create(user=user, mobile_number='123456789')

        response = self.client.get('/users/?mobile_number=987654321')
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)

        response = self.client.get("/users/?mobile_number=" + userprofile.mobile_number)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

    def test_check_username(self):
        user = User.objects.create(username='some_other_name')

        response = self.client.get('/users/?username=rajni')
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)

        response = self.client.get("/users/?username=" + user.username)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

    def test_check_email(self):
        user = User.objects.create(email='haha@ha.ha')
        self.client.login(username='Rajni', password='I_suck')

        response = self.client.get('/users/?email=bla@bla.bl')
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)

        response = self.client.get("/users/?email=" + user.email)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

    def test_list_users(self):
        user = User.objects.create()
        response = self.client.get('/users/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('users/index.html', templates)
        self.assertEqual(len(response.context['users']), 3)
        self.assertIn(user, response.context['users'])
        self.assertNotEqual(None, response.context['request'])

    def test_edit_user_view(self):
        user = User.objects.create_user('andrew', 'a@m.vom', 'pass')
        UserProfile.objects.create(user=user, mobile_number='200202020')
        url = "/users/"+str(user.pk)+"/edit/"
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('users/new.html', templates)
        self.assertEquals(response.context['action'], url)
        self.assertEquals(response.context['id'], 'edit-user-form')
        self.assertEquals(response.context['title'], 'Edit User')
        self.assertEquals(response.context['button_label'], 'Save Changes')
        self.assertEquals(response.context['loading_text'], 'Saving...')
        self.assertEquals(response.context['country_phone_code'], '256')
        self.assertIsInstance(response.context['userform'], EditUserForm)

    def test_edit_user_updates_user_information(self):
        form_data = {
                    'username':'knight',
                    'password1':'mk',
                    'password2':'mk',
                    'first_name':'michael',
                    'last_name':'knight',
                    'mobile_number':'123456789',
                    'email':'mm@mm.mm',
                }
        self.failIf(User.objects.filter(username=form_data['username']))
        user = User.objects.create(username=form_data['username'], email=form_data['email'], password=form_data['password1'])
        UserProfile.objects.create(user=user, mobile_number=form_data['mobile_number'])

        data = {
                    'username':'knight',
                    'password1':'mk',
                    'password2':'mk',
                    'first_name':'michael',
                    'last_name':'knightngale',
                    'mobile_number':'123456789',
                    'email':'mm@mm.mm',
                }

        response = self.client.post('/users/'+str(user.pk)+'/edit/', data=data)
        self.failUnlessEqual(response.status_code, 302)
        edited_user = User.objects.filter(last_name='knightngale')
        self.assertEqual(len(edited_user), 1)

    @patch('survey.views.users._add_error_messages')
    def test_edit_username_not_allowed(self, mock_add_error_messages):
        form_data = {
                    'username':'knight',
                    'password1':'mk',
                    'password2':'mk',
                    'first_name':'michael',
                    'last_name':'knight',
                    'mobile_number':'123456789',
                    'email':'mm@mm.mm',
                }
        self.failIf(User.objects.filter(username=form_data['username']))
        user = User.objects.create(username=form_data['username'], email=form_data['email'], password=form_data['password1'])
        UserProfile.objects.create(user=user, mobile_number=form_data['mobile_number'])

        data = form_data.copy()
        data['username'] = 'changed'
        response = self.client.post('/users/'+str(user.pk)+'/edit/', data=data)
        self.failUnlessEqual(response.status_code, 200)
        edited_user = User.objects.filter(username=data['username'])
        self.failIf(edited_user)
        original_user = User.objects.filter(username=form_data['username'], email=form_data['email'])
        self.failUnless(original_user)
        assert mock_add_error_messages.is_called
    
    def test_current_user_edits_his_own_profile(self):
        form_data = {
                    'username':'knight',
                    'password1':'mk',
                    'password2':'mk',
                    'first_name':'michael',
                    'last_name':'knight',
                    'mobile_number':'123456789',
                    'email':'mm@mm.mm',
                }
        self.failIf(User.objects.filter(username=form_data['username']))
        user_without_permission = User.objects.create(username=form_data['username'], email=form_data['email'])
        user_without_permission.set_password(form_data['password1'])
        user_without_permission.save()
        UserProfile.objects.create(user=user_without_permission, mobile_number=form_data['mobile_number'])

        self.client.logout()
        self.client.login(username=form_data['username'], password=form_data['password1'])

        data = {
                    'username':'knight',
                    'first_name':'michael',
                    'last_name':'knightngale',
                    'mobile_number':'123456789',
                    'email':'mm@mm.mm',
                }

        response = self.client.post('/users/'+str(user_without_permission.pk)+'/edit/', data=data)
        self.failUnlessEqual(response.status_code, 302)
        edited_user = User.objects.filter(last_name='knightngale')
        self.assertEqual(len(edited_user), 1)

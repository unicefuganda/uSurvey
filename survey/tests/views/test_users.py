import json

from django.test import TestCase
from django.test.client import Client
from mock import *

from survey.models import *
from django.contrib.auth.models import User, Group


class UsersViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user(username='Rajni', email='rajni@kant.com', password='I_Rock')
        raj.is_superuser=True
        raj.save()
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
        self.assertEquals(response.context['userform'].__class__.__name__, 'UserForm')

    @patch('django.contrib.messages.success')
    def test_create_users(self, success_message):
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
        response = self.client.post('/users/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 302)

        user = User.objects.get(username=form_data['username'])
        self.failUnless(user.id)
        for key in ['username', 'password',  'first_name', 'last_name', 'email']:
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

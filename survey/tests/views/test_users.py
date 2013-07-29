import json

from django.test import TestCase
from django.test.client import Client
from mock import *

from survey.models import *
from django.contrib.auth.models import User


class UsersViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user(username='Rajni', email='rajni@kant.com', password='I_Rock')
        raj.is_superuser=True
        raj.save()
        self.client.login(username='Rajni', password='I_Rock')

    def test_new(self):
        response = self.client.get('/accounts/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('accounts/new.html', templates)
        self.assertEquals(response.context['action'], '/accounts/new/')
        self.assertEquals(response.context['id'], 'create-user-form')
        self.assertEquals(response.context['button_label'], 'Create User')
        self.assertEquals(response.context['loading_text'], 'Creating...')
        self.assertIsNotNone(response.context['form'])


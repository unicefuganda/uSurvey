from django.test.client import Client
from django.contrib.auth.models import User

from survey.views.aggregates import *
from survey.tests.base_test import BaseTest

class AggregatesPageTest(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user(
            'Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_aggregates')
        self.client.login(username='Rajni', password='I_Rock')

    def test_is_valid_params(self):
        self.assertTrue(is_valid({'location': '1', 'batch': '2'}))

    def test_empty_location_is_also_valid(self):
        self.assertTrue(is_valid({'location': '', 'batch': '2'}))

    def test_invalid(self):
        self.assertFalse(is_valid({'batch': '2'}))
        self.assertFalse(is_valid({'location': '2', 'batch': 'NOT_A_DIGIT'}))
        self.assertFalse(is_valid({'location': 'NOT_A_DIGIT', 'batch': '1'}))
        self.assertFalse(is_valid({'location': '1'}))
import json

from django.test import TestCase
from django.test.client import Client
from mock import *
from django.template.defaultfilters import slugify

from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import *
from survey.views.views_helper import initialize_location_type, assign_immediate_child_locations, update_location_type
from django.contrib.auth.models import User


class UserViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        self.client.login(username='Rajni', password='I_Rock')
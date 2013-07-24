import json

from django.test import TestCase
from django.test.client import Client
from mock import *
from survey.views.home_page import *


class HomepageViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        response = self.client.get('/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/about.html', templates)

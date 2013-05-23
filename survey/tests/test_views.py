from django.test import TestCase
from django.test.client import Client

class InvestigatorsViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_new(self):
        response = self.client.get('/investigators/new')
        self.failUnlessEqual(response.status_code, 200)
        templates = [ template.name for template in response.templates]
        self.assertIn('investigators/new.html', templates)
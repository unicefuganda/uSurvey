from django.test import TestCase
from django.test.client import Client


class HomepageViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        response = self.client.get('/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/index.html', templates)

    def test_about_page(self):
        response = self.client.get('/about/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/about.html', templates)

    def test_map_page(self):
        response = self.client.get('/home/completion/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/map.html', templates)
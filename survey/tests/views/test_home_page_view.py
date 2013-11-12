from django.test import TestCase
from django.test.client import Client
from survey.models import Survey


class HomepageViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        survey_1 = Survey.objects.create(name="A")
        survey_2 = Survey.objects.create(name="B")
        response = self.client.get('/')
        self.assertIn(survey_1, response.context['surveys'])
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/index.html', templates)
        self.assertIn(survey_2, response.context['surveys'])

    def test_about_page(self):
        response = self.client.get('/about/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/about.html', templates)
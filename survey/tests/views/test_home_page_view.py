from django.contrib.auth.models import User
from django.test.client import Client
from survey.forms.aboutus_form import AboutUsForm
from survey.models import Survey, AboutUs
from survey.tests.base_test import BaseTest


class HomepageViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_users')
        self.client.login(username='Rajni', password='I_Rock')

    def test_home_page(self):
        survey_1 = Survey.objects.create(name="A")
        survey_2 = Survey.objects.create(name="B")
        response = self.client.get('/')
        self.assertIn(survey_1, response.context['surveys'])
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/index.html', templates)
        self.assertIn(survey_2, response.context['surveys'])

    def test_no_content_available_on_about_page(self):
        response = self.client.get('/about/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/about.html', templates)

        about_us = AboutUs.objects.all()[0]
        self.assertEqual(about_us, response.context['about_content'])
        self.assertEqual(about_us.content, 'No content available yet !!')

    def test_about_page(self):
        about_us_content = AboutUs.objects.create(content="blah blah")
        response = self.client.get('/about/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/about.html', templates)
        self.assertEqual(about_us_content, response.context['about_content'])

    def test_get_edit_about_page(self):
        about_us_content = AboutUs.objects.create(content="blah blah")
        response = self.client.get('/about/edit/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/edit.html', templates)
        self.assertEqual(about_us_content, response.context['about_form'].instance)
        self.assertIsInstance(response.context['about_form'], AboutUsForm)

    def test_post_edit_about_page(self):
        about_us_content = AboutUs.objects.create(content="blah blah")
        form_data = {'content': about_us_content.content + "more blah blah blah"}
        self.failIf(AboutUs.objects.filter(**form_data))
        response = self.client.post('/about/edit/', data=form_data)
        self.assertRedirects(response, '/about/')
        self.failUnless(AboutUs.objects.filter(**form_data))
        message = "About us content successfully updated"
        self.assertIn(message, response.cookies['messages'].value)

    def test_restricted_permssion(self):
        AboutUs.objects.create(content="blah blah")
        self.assert_restricted_permission_for('/about/edit/')

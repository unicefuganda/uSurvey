from django.contrib.auth.models import User
from django.test.client import Client
from survey.forms.aboutus_form import AboutUsForm
from survey.models import Survey, AboutUs, SuccessStories
from survey.tests.base_test import BaseTest
from django.core.urlresolvers import reverse


class HomepageViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='demo3@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(
            User.objects.create_user(
                'demo3',
                'demo3@kant.com',
                'demo3'),
            'can_view_users')
        self.client.login(username='demo3', password='demo3')

    def test_home_page(self):
        response = self.client.get('/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('main/index.html', templates)

    def test_no_content_available_on_about_page(self):
        response = self.client.get(reverse('about_page'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('main/about.html', templates)

        about_us = AboutUs.objects.all()[0]
        self.assertEqual(about_us, response.context['about_content'])
        self.assertEqual(about_us.content, 'No content available yet !!')

    def test_about_page(self):
        about_us_content = AboutUs.objects.create(content="blah blah")
        response = self.client.get(reverse('about_page'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('main/about.html', templates)
        self.assertEqual(about_us_content, response.context['about_content'])

    def test_get_edit_about_page(self):
        about_us_content = AboutUs.objects.create(content="blah blah")
        response = self.client.get(reverse('edit_about_page'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('home/edit.html', templates)
        self.assertEqual(about_us_content, response.context[
                         'about_form'].instance)
        self.assertIsInstance(response.context['about_form'], AboutUsForm)

    def test_post_edit_about_page(self):
        about_us_content = AboutUs.objects.create(content="blah blah")
        form_data = {'content': about_us_content.content +
                     "more blah blah blah"}
        self.failIf(AboutUs.objects.filter(**form_data))
        response = self.client.post(reverse('edit_about_page'), data=form_data)
        self.assertRedirects(response, reverse('about_page'))
        self.failUnless(AboutUs.objects.filter(**form_data))
        message = "About us content successfully updated"
        self.assertIn(message, response.cookies['messages'].value)

    def test_restricted_permssion(self):
        AboutUs.objects.create(content="blah blah")
        self.assert_restricted_permission_for(reverse('edit_about_page'))

    def test_success_story_page(self):
        ss_content = SuccessStories.objects.create(name='abc',content="blah blah",image='1.jpg')
        response = self.client.get(reverse('home_success_story_list'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('main/home_success_story_list.html', templates)
        self.assertIn(ss_content, response.context['ss_list'])

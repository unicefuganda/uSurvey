from model_mommy import mommy
import os
from django.contrib.auth.models import User, Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from survey.forms.aboutus_form import AboutUsForm
from survey.models import *
from survey.utils.views_helper import has_super_powers
from survey.views.home_page import custom_400, custom_403, custom_404, custom_500
from survey.tests.base_test import BaseTest


class HomepageViewTest(BaseTest):
    fixtures = ['enumeration_area', 'locations', 'location_types', 'contenttypes', 'groups', 'permissions', ]

    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='demo3@kant.com', password='I_Suck')
        self.user = User.objects.create_user('demo13', 'demo3@kant.com', 'demo13')
        self.user.user_permissions.add(Permission.objects.get(codename='can_have_super_powers'))
        self.user.user_permissions.add(Permission.objects.get(codename='can_view_users'))
        self.client.login(username='demo13', password='demo13')

    def test_home_page(self):
        survey_obj = mommy.make(Survey)
        url = reverse('main_page')
        url = url+'?survey%s'%survey_obj.id
        response = self.client.get(url)
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

    def test_activate_super_powers(self):
        url = reverse('activate_super_powers_page')
        response = self.client.get(url, follow=True)
        self.assertTrue(reverse('login_page') in response.context['request'].path
                        or has_super_powers(response.context['request']))    # logs out first
        self.client.login(username='demo13', password='demo13')
        response = self.client.get(url, follow=True)
        self.assertTrue(has_super_powers(response.context['request']))
        # now deactiate
        url = reverse('deactivate_super_powers_page')
        response = self.client.get(url, follow=True)
        self.assertFalse(has_super_powers(response.context['request']))

    def test_home_page(self):
        url = reverse('home_page')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertIn('map_filter', response.context)

    def test_success_list_page(self):
        mommy.make(SuccessStories)
        second = mommy.make(SuccessStories)
        mommy.make(SuccessStories)
        url = reverse('success_story_list')
        response = self.client.get(url)
        self.assertEquals(response.context['ss_list'].count(), 3)
        # test delete
        url = reverse('success_story_delete', args=(second.id, ))
        response = self.client.get(url, follow=True)
        self.assertEquals(response.context['ss_list'].count(), 2)
        self.assertEquals(response.context['ss_list'].filter(id=second.id).count(), 0)

    def test_update_success_message(self):
        BASE_DIR = os.path.dirname(__file__)
        image_path = os.path.join(BASE_DIR, 'testimage.png')
        story = mommy.make(SuccessStories)
        fi = open(image_path)
        fi_content = fi.read()
        sfi = SimpleUploadedFile(fi.name, fi_content)
        url = reverse('success_story_edit', args=(story.id, ))
        data = {'image': sfi, 'name': 'new edited', }
        response = self.client.post(url, data=data)
        self.assertEquals(SuccessStories.objects.count(), 1)
        self.assertFalse(response.context['form'].is_valid())       # content not present invalid form
        data['content'] = 'Test edited content'
        sfi = SimpleUploadedFile(fi.name, fi_content)
        data['image'] = sfi
        response = self.client.post(url, data=data)
        self.assertEquals(SuccessStories.objects.count(), 1)
        db_refreshed = SuccessStories.objects.first()
        self.assertEquals(db_refreshed.name, data['name'])
        self.assertEquals(db_refreshed.content, data['content'])

    def test_custom_pages(self):
        request = RequestFactory().get('/')
        response = custom_500(request)
        self.assertEquals(response.status_code, 500)
        response = custom_400(request)
        self.assertEquals(response.status_code, 400)
        response = custom_404(request)
        self.assertEquals(response.status_code, 404)
        response = custom_403(request)
        self.assertEquals(response.status_code, 302)
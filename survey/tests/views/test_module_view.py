import json
from django.core.urlresolvers import reverse
from django.test.client import Client
from mock import *

from django.contrib.auth.models import User, Group
from survey.models import QuestionModule

from survey.forms.question_module_form import QuestionModuleForm

from survey.tests.base_test import BaseTest




class ListingViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.user_without_permission = User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        self.raj = self.assign_permission_to(User.objects.create_user(
            'Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_users')
        self.client.login(username='Rajni', password='I_Rock')
        self.form_data = {
            'name': 'New module',
            'description': 'module description rajni',
        }

    def test_add_module(self):
        response = self.client.get(reverse('new_question_module_page'))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('question_module/new.html', templates)
        self.assertIsInstance(response.context['question_module_form'], QuestionModuleForm)
        self.assertIn('Create', response.context['button_label'])
        self.assertIn('add-question_set-form', response.context['id'])
        self.assertIn('New Module', response.context['title'])
        self.assertIn(reverse('new_question_module_page'), response.context['action'])

    def test_index(self):
        response = self.client.get(reverse('question_module_listing_page'))
        self.failUnlessEqual(response.status_code, 200)


    def test_view_module_list(self):
        list_1 = QuestionModule.objects.create(name="Module A")
        list_2 = QuestionModule.objects.create(name="Module B")
        response = self.client.get(reverse('question_module_listing_page'))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('question_module/index.html', templates)
        self.assertIn(list_1, response.context['question_modules'])
        self.assertIn(list_2, response.context['question_modules'])
        self.assertIsNotNone(response.context['request'])

    def test_new_should_create_module_on_post(self):
        form_data = self.form_data
        all_listings = QuestionModule.objects.filter(**form_data)
        self.failIf(all_listings)
        response = self.client.post(reverse('new_question_module_page'), data=form_data)
        self.assertRedirects(response, expected_url=reverse('question_module_listing_page'), status_code=302, target_status_code=200,
                             msg_prefix='')
        retrieved_listing = QuestionModule.objects.filter(**form_data)
        self.assertEquals(1, len(retrieved_listing))
        self.assertIn('Question module successfully created.',
                      response.cookies['messages'].__str__())

    def test_delete_should_delete_the_module(self):
        listing = QuestionModule.objects.create(**self.form_data)
        self.failUnless(listing)

        response = self.client.get(reverse('delete_question_module_page',kwargs={"module_id":listing.id}))

        self.assertRedirects(
            response, reverse('question_module_listing_page'), status_code=302, target_status_code=200, msg_prefix='')

    def test_module_does_not_exist(self):
        message = "Listing does not exist."
        self.assert_object_does_not_exist(reverse('edit_question_module_page',kwargs={"module_id":500}), message)
    

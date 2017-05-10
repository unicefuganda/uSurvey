import json
from django.core.urlresolvers import reverse
from django.test.client import Client
from mock import *

from django.contrib.auth.models import User, Group
from survey.models import ListingTemplate, QuestionSet

from survey.forms.question_set import get_question_set_form

from survey.tests.base_test import BaseTest

questionSetForm = get_question_set_form(QuestionSet)




class ListingViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.user_without_permission = User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        self.raj = self.assign_permission_to(User.objects.create_user(
            'Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_users')
        self.client.login(username='Rajni', password='I_Rock')
        self.form_data = {
            'name': 'survey rajni',
            'description': 'listing description rajni',
            'access_channels': 'Odk Access'
        }

    def test_add_listing(self):
        response = self.client.get(reverse('new_listing_template_page'))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/new.html', templates)
        self.assertIsInstance(response.context['question_set_form'], questionSetForm)
        self.assertIn('Create', response.context['button_label'])
        self.assertIn('add-question_set-form', response.context['id'])
        self.assertIn('New Listing Form', response.context['title'])
        self.assertIn('question_set/new/', response.context['action'])

    def test_index(self):
        response = self.client.get(reverse('listing_template_home'))
        self.failUnlessEqual(response.status_code, 200)


    def test_view_Listing_list(self):
        list_1 = ListingTemplate.objects.create(name="List A", access_channels='Odk Access')
        list_2 = ListingTemplate.objects.create(name="List B", access_channels='USSD Access')
        response = self.client.get(reverse('listing_template_home'))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/index.html', templates)
        self.assertIn(list_1, response.context['question_sets'])
        self.assertIn(list_2, response.context['question_sets'])
        self.assertIsNotNone(response.context['request'])
        self.assertIsInstance(response.context['question_set_form'], questionSetForm)

    def test_new_should_create_listing_on_post(self):
        form_data = self.form_data
        all_listings = ListingTemplate.objects.filter(**form_data)
        self.failIf(all_listings)
        response = self.client.post(reverse('new_listing_template_page'), data=form_data)
        self.assertRedirects(response, expected_url=reverse('listing_template_home'), status_code=302, target_status_code=200,
                             msg_prefix='')
        retrieved_listing = ListingTemplate.objects.filter(**form_data)
        self.assertEquals(1, len(retrieved_listing))
        self.assertIn('Listing Form successfully added.',
                      response.cookies['messages'].__str__())


    def test_new_should_not_create_listing_on_post_if_listing_with_same_name_exists(self):
        form_data = self.form_data

        ListingTemplate.objects.create(**form_data)

        response = self.client.post(reverse('new_listing_template_page'), data=form_data)
        error_message = "Listing with name %s already exist." % form_data[
            'name']
        self.assertIn(error_message, response.context[
                      'question_set_form'].errors['name'])



    def test_edit_should_get_form_with_data_of_the_listing(self):
        listing = ListingTemplate.objects.create(**self.form_data)
        self.failUnless(listing)
        response = self.client.get(reverse('edit_listing_template_page', kwargs={'qset_id':listing.id}))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/new.html', templates)
        self.assertIsInstance(response.context['question_set_form'], SurveyForm)
        self.assertIn('edit-question_set_form', response.context['id'])
        self.assertIn('Save', response.context['button_label'])
        self.assertIn('Edit Listing', response.context['title'])
        self.assertIn(reverse('edit_listing_template_page', kwargs={'qset_id':listing.id}), response.context['action'])

    def test_edit_should_post_should_edit_the_listing(self):
        listing = ListingTemplate.objects.create(**self.form_data)
        self.failUnless(listing)
        form_data = self.form_data
        form_data['name'] = 'edited_name'
        form_data['description'] = 'edited_description'

        response = self.client.post(reverse('edit_listing_template_page', kwargs={'qset_id':listing.id}), data=form_data)
        self.failIf(ListingTemplate.objects.filter(name=listing.name))

        listing = ListingTemplate.objects.get(
            name=form_data['name'], description=form_data['description'])
        self.failUnless(listing)
        self.assertRedirects(
            response, reverse('listing_template_home'), status_code=302, target_status_code=200, msg_prefix='')
        success_message = "Listing Form successfully edited."
        self.assertIn(success_message, response.cookies['messages'].value)


    def test_delete_should_delete_the_listing(self):
        listing = ListingTemplate.objects.create(**self.form_data)
        self.failUnless(listing)

        response = self.client.get(reverse('delete_listing_template',kwargs={"qset_id":listing.id}))

        self.assertRedirects(
            response, reverse('listing_template_home'), status_code=302, target_status_code=200, msg_prefix='')

    def test_listing_does_not_exist(self):
        message = "Listing Form does not exist."
        self.assert_object_does_not_exist(reverse('edit_listing_template_page',kwargs={"qset_id":500}), message)

    def test_should_throw_error_if_deleting_non_existing_listng(self):
        message = "Listing Form does not exist."
        self.assert_object_does_not_exist(reverse('delete_listing_template',kwargs={"qset_id":500}), message)


    def insert_qset_index(self):
        response = self.client.get(reverse('qset_questions_page'))
        self.failUnlessEqual(response.status_code, 200)

    def test_restricted_permission(self):
        url = reverse('listing_template_home')
        self.assert_restricted_permission_for(url)
        url =reverse('new_listing_template_page')
        self.assert_restricted_permission_for(url)
        url =reverse('edit_listing_template_page', kwargs={'qset_id':listing.id})
        self.assert_restricted_permission_for(url)
        url = reverse('delete_listing_template',kwargs={"qset_id":500})
        self.assert_restricted_permission_for(url)


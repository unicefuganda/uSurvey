import json
from django.core.urlresolvers import reverse
from django.test.client import Client
from mock import *
from django.contrib.auth.models import User, Group
from survey.models import ListingTemplate, QuestionSet
from survey.forms.question_set import get_question_set_form
from survey.forms.question import get_question_form
from survey.tests.base_test import BaseTest

questionSetForm = get_question_set_form(QuestionSet)

class ListingViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.user_without_permission = User.objects.create_user(
            username='useless', email='demo6@kant.com', password='I_Suck')
        self.raj = self.assign_permission_to(User.objects.create_user(
            'demo6', 'demo6@kant.com', 'demo6'), 'can_view_batches')
        self.client.login(username='demo6', password='demo6')
        self.form_data = {
            'name': 'survey demo6',
            'description': 'listing description demo6'
        }
        self.qset_list = QuestionSet.objects.create(
            name='qset name', description='qset descrpition')

    def test_add_listing(self):
        response = self.client.get(reverse('new_listing_template_page'))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/new.html', templates)
        self.assertIn('Create', response.context['button_label'])
        self.assertIn('add-question_set-form', response.context['id'])
        self.assertIn('New Listing Form', response.context['title'])

    def test_index(self):
        response = self.client.get(reverse('listing_template_home'))
        self.assertEqual(200, response.status_code)

    def test_view_Listing_list(self):
        list_1 = ListingTemplate.objects.create(name="List A")
        list_2 = ListingTemplate.objects.create(name="List B")
        response = self.client.get(reverse('listing_template_home'))
        self.assertIn(response.status_code, [200,302])
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/index.html', templates)
        self.assertIn(list_1, response.context['question_sets'])
        self.assertIn(list_2, response.context['question_sets'])
        self.assertIsNotNone(response.context['request'])

    def test_new_should_create_listing_on_post(self):
        form_data = self.form_data
        all_listings = ListingTemplate.objects.filter(**form_data)
        self.failIf(all_listings)
        response = self.client.post(reverse('new_listing_template_page'), data=form_data)
        self.assertIn(response.status_code, [200,302])
        # self.assertRedirects(response, expected_url=reverse('listing_template_home'), status_code=302, target_status_code=200,
        #                      msg_prefix='')

    def test_edit_should_get_form_with_data_of_the_listing(self):
        listing = ListingTemplate.objects.create(**self.form_data)
        self.failUnless(listing)
        response = self.client.get(reverse('edit_listing_template_page', kwargs={'qset_id':listing.id}))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/new.html', templates)
        self.assertIn('edit-question-set-form', response.context['id'])
        self.assertIn('name, description',response.context['placeholder'])

    def test_edit_should_post_should_edit_the_listing(self):
        listing = ListingTemplate.objects.create(name="sudh",description="desc")
        self.failUnless(listing)
        form_data = self.form_data
        form_data['name'] = 'edited_name'
        form_data['description'] = 'edited_description'
        response = self.client.post(reverse('edit_listing_template_page', kwargs={'qset_id':listing.id}), data=form_data)
        self.failIf(ListingTemplate.objects.filter(name=listing.description))
        listing = ListingTemplate.objects.get(
            name='sudh', description='desc')
        self.failUnless(listing)
        self.assertIn(response.status_code, [200,302])
        # self.assertRedirects(
        #     response, reverse('listing_template_home'), status_code=302, target_status_code=200, msg_prefix='')
        # success_message = "Listing Form successfully edited."
        # self.assertIn(success_message, response.cookies['messages'].value)

    def test_delete_should_delete_the_listing(self):        
        listing = ListingTemplate.objects.create(name="listing_name", description="list_description")        
        self.failUnless(listing)
        response = self.client.get(reverse('delete_listing_template',kwargs={"qset_id":listing.id}))
        self.assertRedirects(
            response, reverse('listing_template_home'), status_code=302, target_status_code=200, msg_prefix='')

    def insert_qset_index(self):
        response = self.client.get(reverse('qset_questions_page'))
        self.failUnlessEqual(response.status_code, 200)

    # def test_restricted_permission(self):
    #     url = reverse('listing_template_home')
    #     self.assert_restricted_permission_for(url)
    #     url =reverse('new_listing_template_page')
    #     self.assert_restricted_permission_for(url)
    #     listing = ListingTemplate.objects.create(**self.form_data)
    #     url =reverse('edit_listing_template_page', kwargs={'qset_id':listing.id})
    #     self.assert_restricted_permission_for(url)
    #     url = reverse('delete_listing_template',kwargs={"qset_id":500})
    #     self.assert_restricted_permission_for(url)

    # def test_add_listing_question(self):
    #     list_1 = ListingTemplate.objects.create(name="List A1")
    #     response = self.client.get(reverse('new_qset_question_page', kwargs={'qset_id':list_1.id}))
    #     self.assertEqual(200, response.status_code)
    #     templates = [template.name for template in response.templates]
    #     self.assertIn('set_questions/new.html', templates)
    #     batch = QuestionSet.get(pk=list_1)
    #     QuestionForm = get_question_form(batch.question_model())
    #     self.assertIsInstance(response.context['questionform'], QuestionForm)
    #     self.assertIn('Create', response.context['button_label'])
    #     self.assertIn('add-question-form', response.context['id'])
    #     self.assertIn('New Listing Form', response.context['title'])
    #     self.assertIn('question_set/new/', response.context['action'])
    #     self.assertIn(batch, response.context['batch'])
    #     self.assertIn('question-form', response.context['class'])

    # def test_new_should_create_listing_question_on_post(self):
    #     list_1 = ListingTemplate.objects.create(name="List A2")
    #     batch = QuestionSet.get(pk=list_1)
    #     form_data = {'identifier':'i_1',
    #     'text':'blah blah',
    #     'answer_type':'Text Answer',
    #     'mandatory':1,
    #     'qset':batch
    #     }  
    #     q_list = QuestionSet.objects.filter(**form_data)
    #     self.failIf(q_list)
    #     response = self.client.post(reverse('new_qset_question_page', kwargs={'qset_id':retrieved_listing.id}), data=form_data)
    #     self.assertRedirects(response, expected_url=reverse('qset_questions_page'), status_code=302, target_status_code=200,
    #                          msg_prefix='')
    #     r_q_list = QuestionSet.objects.filter(**form_data)
    #     self.assertEquals(1, len(r_q_list))

    def test_restricted_permssion(self):
        form_data = self.form_data       
        q = QuestionSet.objects.filter(**form_data)
        self.assert_restricted_permission_for(reverse('listing_template_home'))
        self.assert_restricted_permission_for(reverse('new_listing_template_page'))
        self.assert_restricted_permission_for(
            '/listing_form/edit/%d/' % self.qset_list.id)
        self.assert_restricted_permission_for(
            '/listing_form/delete/%d/' % self.qset_list.id)
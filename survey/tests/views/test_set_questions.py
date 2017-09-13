import json
from model_mommy import mommy
from django.contrib.auth.models import User
from model_mommy import mommy
from django.test.client import Client
from django.core.urlresolvers import reverse
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import (QuestionModule, Interviewer,  EnumerationArea, QuestionTemplate, NumericalAnswer,
                           TextAnswer, MultiChoiceAnswer, DateAnswer, QuestionOption, Interview, ListingTemplate,
                           ODKAccess, Question, QuestionSet,Batch, ResponseValidation)
from survey.utils.query_helper import get_filterset
from survey.tests.base_test import BaseTest

class SetQuestionViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.listing_data = {'name': 'test-listing', 'access_channels': [ODKAccess.choice_name(), ], }

        self.questions_data = []
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest",constraint_message="message")
        # create a inline flows for this listing
        for answer_class in [NumericalAnswer, TextAnswer, DateAnswer, MultiChoiceAnswer]:
            self.questions_data.append({'text': 'text: %s' % answer_class.choice_name(),
                                        'answer_type': answer_class.choice_name(),
                                        'identifier': 'id: %s' % answer_class.choice_name()})
        self.questions_data[-1]['options'] = ['Yes', 'No']
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.client.login(username='demo12', password='demo12')
        self.listing_form_data = {
            'name': 'test listing1',
            'description': 'listing description demo6'            
        }
        self.qset_form_data = {
            'name': 'test listing1 q1',
            'description': 'listing description demo6',
        }


    def test_view_questions_list(self):
        list_1 = ListingTemplate.objects.create(**self.listing_form_data)
        response = self.client.get(reverse('listing_template_home'))
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse('qset_questions_page', kwargs={'qset_id':list_1.id}))
        self.assertEqual(200, response.status_code)
        # templates = [ template.name for template in response.templates ]
        # self.assertIn('set_questions/index.html', templates)

        # self.assertIn(survey_1, response.context['surveys'])
        # self.assertIn(survey_2, response.context['surveys'])
        # self.assertIsNotNone(response.context['request'])
        # self.assertIsInstance(response.context['survey_form'], SurveyForm)
    
    def test_add_question(self):
        list_1 = ListingTemplate.objects.create(name="List A2")
        batch = QuestionSet.get(pk=list_1.id)        
        qset1 = QuestionSet.objects.create(name="dummy", description="bla bla")
        response = self.client.get(reverse('qset_questions_page', kwargs={'qset_id':list_1.id}))
        self.assertEqual(200, response.status_code)
        templates = [ template.name for template in response.templates ]
        self.assertIn('set_questions/index.html', templates)
        self.assertNotIn('Add Question', response.context['title'])        
        self.assertNotIn(reverse('qset_questions_page', kwargs={'qset_id':list_1.id}), response.context['action'])
    
    def test_question_doesnotexist(self):
        response = self.client.get(reverse('qset_questions_page', kwargs={'qset_id':99999}))
        self.assertEqual(404, response.status_code)       
        try:
            qf = QuestionSet.objects.get(name="dummy1", description="bla bla")
            self.assertTrue(True)
        except QuestionSet.DoesNotExist as e:
            self.assertFalse(False)
            self.assertEquals(str(e),"QuestionSet matching query does not exist.")
            pass
    def test_question_filters(self):
        search_fields = ['identifier', 'text', ]
        qset1 = QuestionSet.objects.create(name="q2", description="bla bla")
        batch = QuestionSet.get(pk=qset1.id)
        q1 = Question.objects.create(identifier='123.1', text="This is a question123.1", answer_type='Numerical Answer',
                                                  qset_id=qset1.id, response_validation_id=1)
        
        #response = self.client.get(reverse('qset_questions_page', kwargs={'qset_id':qset1.id}))
        q = 'q2'
        qset_questions = batch.questions.all()
        filter_result = get_filterset(qset_questions, q, search_fields)
        print filter_result
        self.assertIn(qset1, filter_result)        
    
    def test_new_subquestion(self):
        list_1 = ListingTemplate.objects.create(name="List A2")
        batch = QuestionSet.get(pk=list_1.id)
        batch =  Batch.objects.create(name="batchname")
        qset = QuestionSet.objects.create(name="qset", description="bla")


    def test_add_listing(self):
        create_qset_url = reverse('new_%s_page' % ListingTemplate.resolve_tag())
        response = self.client.post(create_qset_url, data=self.listing_data)
        self.assertEquals(ListingTemplate.objects.count(), 1)
        self.assertEquals(ListingTemplate.objects.first().name, self.listing_data['name'])
    
    # def test_new_subquestion(self):
    #     batch =  Batch.objects.create(name="batchname")
    #     qset = QuestionSet.objects.create(name="qset", description="bla")

    def text_add_question_fails_if_id_has_space(self):
        self.test_add_listing()
        listing = ListingTemplate.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(listing.pk, ))
        data = self.questions_data[0]
        response = self.client.post(create_sq_url, data=data)
        self.assertIn(Question.objects.count(), 0)
        self.assertIn('questionform' in response.context)
        self.assertEquals(response.context['questionform'].is_valid(), False)

    def test_add_question_to_listing(self):
        self.test_add_listing()
        listing = ListingTemplate.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(listing.pk, ))
        for data in self.questions_data:
            data['identifier'] = data['identifier'].replace(':', '').replace(' ', '')
            data['qset'] = listing.pk
            response = self.client.post(create_sq_url, data=data)
            question = Question.objects.order_by('created').last()
            self.assertEquals(question.text, data['text'])
            self.assertEquals(question.identifier, data['identifier'])
            self.assertEquals(question.answer_type, data['answer_type'])

    def test_insert_question_to_listing(self):
        self.test_add_question_to_listing()
        self.assertTrue(Question.objects.count() > 2)
        inlines = QuestionSet.objects.first().questions_inline()
        question = inlines[1]
        insert_sq_url = reverse('insert_qset_question_page', args=(question.pk, ))
        data = {'text': 'text: %s' % TextAnswer.choice_name(),
                'answer_type': TextAnswer.choice_name(),
                'identifier': 'test_insert_id',
                'qset': question.qset.pk}
        response = self.client.post(insert_sq_url, data=data)
        self.assertTrue(response.status_code, 302)
        inlines = question.qset.questions_inline()
        self.assertEquals(data['identifier'], inlines[2].identifier)
        self.assertEquals(data['text'], inlines[2].text)
        self.assertEquals(data['answer_type'], inlines[2].answer_type)

    def test_add_to_library_flag_for_add_question_to_listing(self):
        self.test_add_listing()
        listing = ListingTemplate.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(listing.pk, ))
        data = self.questions_data[0]
        data['add_to_lib_button'] = 1
        data['qset'] = listing.pk
        data['identifier'] = data['identifier'].replace(':', '').replace(' ', '')
        response = self.client.post(create_sq_url, data=data)
        question = Question.objects.order_by('created').last()
        self.assertEquals(question.text, data['text'])
        self.assertEquals(question.identifier, data['identifier'])
        self.assertEquals(question.answer_type, data['answer_type'])
        question_template = QuestionTemplate.objects.first()
        self.assertEquals(question_template.text, data['text'])
        self.assertEquals(question_template.identifier, data['identifier'])
        self.assertEquals(question_template.answer_type, data['answer_type'])

    def test_add_more_button_returns_to_same_page(self):
        self.test_add_listing()
        listing = ListingTemplate.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(listing.pk, ))
        data = self.questions_data[0]
        data['add_more_button'] = 1
        data['qset'] = listing.pk
        data['identifier'] = data['identifier'].replace(':', '').replace(' ', '')
        response = self.client.post(create_sq_url, data=data)
        question = Question.objects.order_by('created').last()
        self.assertEquals(question.text, data['text'])
        self.assertEquals(question.identifier, data['identifier'])
        self.assertEquals(question.answer_type, data['answer_type'])
        question_template = QuestionTemplate.objects.first()
        self.assertIn(create_sq_url, response.url)
    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/qset/questions/1/new/')
        self.assert_restricted_permission_for('/qsets/2/questions/')        
        self.assert_restricted_permission_for('/set_questions/1/edit/')        
        self.assert_restricted_permission_for('/qset/questions/1/insert/')
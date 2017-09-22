from django.test.client import Client
from django.contrib.auth.models import User
from survey.models.batch import Batch
from survey.models import QuestionModule, Survey
from django.core.urlresolvers import reverse
from survey.models.questions import Question
from survey.models.questions import QuestionFlow
from survey.models import (QuestionModule, Interviewer,  EnumerationArea, QuestionTemplate, NumericalAnswer,
                           TextAnswer, MultiChoiceAnswer, DateAnswer, QuestionOption, Interview, ListingTemplate,
                           ODKAccess, Question, QuestionSet,Batch, ResponseValidation, Survey)
from survey.tests.base_test import BaseTest
import json
from model_mommy import mommy
from survey.utils.query_helper import get_filterset
from survey.forms.filters import DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE


class QuestionsViewsTest(BaseTest):

    def setUp(self):
        # self.client = Client()
        # user_without_permission = User.objects.create_user(username='useless', email='demo10@kant.com',
        #                                                    password='I_Suck')
        # raj = self.assign_permission_to(User.objects.create_user('demo10', 'demo10@kant.com', 'demo10'),
        #                                 'can_view_batches')
        # self.client.login(username='demo10', password='demo10')
        
        # self.module = QuestionModule.objects.create(name="Education")
        # self.survey = Survey.objects.create(name="haha")
        # self.batch = Batch.objects.create(
        #     order=1, name="Batch A", survey=self.survey)
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='demo12@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        
        self.listing_obj = mommy.make(ListingTemplate)
        self.qset_obj = QuestionSet.objects.get(pk=self.listing_obj.id)
        self.survey_obj = mommy.make(Survey)
        self.interview_form_data = {"question_set" : self.qset_obj, "survey" : self.survey_obj}
        self.interview_obj = Interview.objects.create(**self.interview_form_data)
        self.rsp_obj = ResponseValidation.objects.create(validation_test="validationtest",constraint_message="message")
        self.ta_form_data = {"question_type" : "abc", "value" : 1,  "identifier" :"a1", "as_text" : "as_text", "as_value" : "as_value", "interview": self.interview_obj}
        self.answer_type = TextAnswer.objects.create(**self.ta_form_data)
        self.question_obj = mommy.make(Question, qset=self.listing_obj, answer_type=NumericalAnswer.choice_name())
        self.client.login(username='demo12', password='demo12')
        self.sub_data={
            'identifier':"dummy",
            'response_validation':'',
            'text' : "dummss",
            'answer_type' : "Text Answer"
        }
        self.form_data = {
            'groups': "All",
            'modules': "All",
            'question_types': "All",
            'number_of_questions_per_page': 50
        }

    def test_get_index_per_batch(self):        
        survey_obj = Survey.objects.create(
            name='survey name', description='survey descrpition')
        batch_obj = Batch.objects.create(
            order=1, name="BatchBC", survey=survey_obj)
        list_1 = ListingTemplate.objects.create(name="List A15")        
        qset = QuestionSet.get(pk=list_1.id)        
        q1 = Question.objects.create(identifier='123.1', text="This is a question123.1", answer_type='Numerical Answer',
                                                  qset_id=batch_obj.id, response_validation_id=1)
        response = self.client.get(reverse('batch_questions_page', kwargs={"batch_id" : q1.id}))
        self.assertIn(response.status_code,[200,302])        
        templates = [ template.name for template in response.templates ]
        self.assertIn('questions/index.html', templates)
        self.assertNotIn('Add Question', response.context['title'])
        self.assertEqual(self.batch, response.context['batch']) 
        self.assertEqual(DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE,
                         response.context['max_question_per_page'])       
        self.assertNotIn(reverse('batch_questions_page', kwargs={'batch_id':list_1.id}), response.context['action'])   

    def test_new_subquestion(self):
        survey_obj = Survey.objects.create(
            name='survey name', description='survey descrpition')
        batch_obj = Batch.objects.create(
            order=1, name="Batch A", survey=survey_obj)        
        list_1 = ListingTemplate.objects.create(name="List A9")
        qset = QuestionSet.get(pk=list_1.id)
        response = self.client.get(reverse('add_batch_subquestion_page', kwargs={"batch_id" : batch_obj.id}))
        self.assertIn(response.status_code,[200,302])

    def test_add_subquestion(self):
        self.sub_data['parent_question'] = self.question_obj.id
        self.sub_data['response_validation'] = self.rsp_obj.id
        self.sub_data['qset'] = self.listing_obj.id
        self.sub_data['answer_type'] = NumericalAnswer.choice_name()
        response = self.client.post(reverse('add_batch_subquestion_page',
            kwargs={"batch_id" : self.listing_obj.id}),
            self.sub_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        templates = [ template.name for template in response.templates ]
        # self.assertIn('questions/index.html', templates)
        print response.cookies
        print response.content
        print templates,"TEMPLATEDD"
        self.assertEqual(200,response.status_code)

    def test_question_filters(self):
        survey_obj = Survey.objects.create(
            name='survey name', description='survey descrpition')
        batch_obj = Batch.objects.create(
            order=1, name="BatchDC", survey=survey_obj)
        search_fields = ['identifier', 'text', ]
        list_1 = ListingTemplate.objects.create(name="ListB10")
        batch = QuestionSet.get(pk=list_1.id)
        q1 = Question.objects.create(identifier='123.1', text="This is a question123.1", answer_type='Numerical Answer',
                                                  qset_id=batch_obj.id, response_validation_id=1)
        
        response = self.client.get(reverse('batch_questions_page', kwargs={'batch_id':batch_obj.id}))
        q = 'q3'
        batch_questions = batch.questions.all()
        filter_result = get_filterset(batch_questions, q, search_fields)
        #self.assertIn(list_1, filter_result)
        response = self.client.get("%s?q=ListB10"%(reverse('batch_questions_page', kwargs={'batch_id':list_1.id})))
        self.assertIn(response.status_code,[200,302])
        response = self.client.get("%s?q=ListB10&question_types=Numerical Answer"%(reverse('batch_questions_page', kwargs={'batch_id':list_1.id})))
        self.assertIn(response.status_code,[200,302])

    def test_get_sub_questions_for_question(self):
        list_1 = ListingTemplate.objects.create(name="ListA31")
        q1 = Question.objects.create(identifier='123.1', text="This is a question123.1", answer_type='Numerical Answer',
                                                  qset_id=list_1.id, response_validation_id=1)
        response = self.client.get(reverse('questions_subquestion_json_page', kwargs={'question_id':q1.id}))
        json_data = [{"text": "This is a question123.1", "identifier": "123.1", "id": "2"}]
        self.assertEqual(json.dumps(json_data), response.content)    
    def test_delete(self):
        self.question_obj = mommy.make(Question, qset=self.listing_obj, answer_type=NumericalAnswer.choice_name())        
        response = self.client.get(reverse('delete_question_page', kwargs={"question_id" : self.question_obj.id}))
        self.assertIn(response.status_code,[200,302])

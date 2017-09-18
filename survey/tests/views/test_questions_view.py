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
from survey.utils.query_helper import get_filterset
from survey.forms.filters import DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE


class QuestionsViewsTest(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='demo10@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('demo10', 'demo10@kant.com', 'demo10'),
                                        'can_view_batches')
        self.client.login(username='demo10', password='demo10')
        
        self.module = QuestionModule.objects.create(name="Education")
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(
            order=1, name="Batch A", survey=self.survey)
        
        self.form_data = {
            'groups': "All",
            'modules': "All",
            'question_types': "All",
            'number_of_questions_per_page': 50
        }

    def test_get_index_per_batch(self):
        # survey_obj = Survey.objects.create(
        #     name='survey name', description='survey descrpition')
        # batch_obj = Batch.objects.create(
        #     order=1, name="BatchBC", survey=survey_obj)
        # response = self.client.get(reverse('batch_questions_page', kwargs={"batch_id" : batch_obj.id}))
        # # response = self.client.get('/batches/%d/questions/' % self.batch.id)
        # # self.failUnlessEqual(response.status_code, 200)
        # self.assertIn(response.status_code,[200,302])
        # templates = [template.name for template in response.templates]
        # self.assertIn('questions/index.html', templates)
        # self.assertEqual(self.batch, response.context['batch'])
        # self.assertEqual(DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE,
        #                  response.context['max_question_per_page'])
        # self.assertIsNotNone(response.context['request'])
        survey_obj = Survey.objects.create(
            name='survey name', description='survey descrpition')
        batch_obj = Batch.objects.create(
            order=1, name="BatchBC", survey=survey_obj)
        #list_1 = ListingTemplate.objects.create(name="List A15")        
        #qset = QuestionSet.get(pk=list_1.id)
        qset = QuestionSet.get(id=batch_id)
        q1 = Question.objects.create(identifier='123.1', text="This is a question123.1", answer_type='Numerical Answer',
                                                  qset_id=list_1.id, response_validation_id=1)
        response = self.client.get(reverse('batch_questions_page', kwargs={"batch_id" : list_1.id}))
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

    def test_question_filters(self):
        survey_obj = Survey.objects.create(
            name='survey name', description='survey descrpition')
        batch_obj = Batch.objects.create(
            order=1, name="BatchDC", survey=survey_obj)
        search_fields = ['identifier', 'text', ]
        list_1 = ListingTemplate.objects.create(name="ListA6")
        batch = QuestionSet.get(pk=list_1.id)
        q1 = Question.objects.create(identifier='123.1', text="This is a question123.1", answer_type='Numerical Answer',
                                                  qset_id=list_1.id, response_validation_id=1)
        
        response = self.client.get(reverse('batch_questions_page', kwargs={'batch_id':batch_obj.id}))
        q = 'q3'
        batch_questions = batch.questions.all()
        filter_result = get_filterset(batch_questions, q, search_fields)
        #self.assertIn(list_1, filter_result)
        response = self.client.get("%s?q=ListA6"%(reverse('batch_questions_page', kwargs={'batch_id':batch_obj.id})))
        self.assertEqual(200, response.status_code)
        response = self.client.get("%s?q=ListA6&question_types=Numerical Answer"%(reverse('batch_questions_page', kwargs={'batch_id':batch_obj.id})))
        self.assertEqual(200, response.status_code)

from django.test.client import Client
from django.contrib.auth.models import User
from survey.models.batch import Batch
from survey.models import QuestionModule, Survey
from survey.models.questions import Question
from survey.models.questions import QuestionFlow

from survey.tests.base_test import BaseTest
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
        response = self.client.get('/batches/%d/questions/' % self.batch.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('questions/index.html', templates)
        self.assertEqual(self.batch, response.context['batch'])
        self.assertEqual(DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE,
                         response.context['max_question_per_page'])
        self.assertIsNotNone(response.context['request'])


    def test_question_filters(self):
        search_fields = ['identifier', 'text', ]
        list_1 = ListingTemplate.objects.create(name="ListA3")
        batch = QuestionSet.get(pk=list_1.id)
        q1 = Question.objects.create(identifier='123.1', text="This is a question123.1", answer_type='Numerical Answer',
                                                  qset_id=list_1.id, response_validation_id=1)
        
        response = self.client.get(reverse('qset_questions_page', kwargs={'qset_id':list_1.id}))
        q = 'q2'
        qset_questions = batch.questions.all()
        filter_result = get_filterset(qset_questions, q, search_fields)
        #self.assertIn(list_1, filter_result)
        response = self.client.get("%s?q=ListA3"%(reverse('qset_questions_page', kwargs={'qset_id':list_1.id})))
        self.assertEqual(200, response.status_code)
        response = self.client.get("%s?q=ListA3&question_types=Numerical Answer"%(reverse('qset_questions_page', kwargs={'qset_id':list_1.id})))
        self.assertEqual(200, response.status_code)

    def test_new_subquestion(self):
        survey_obj = Survey.objects.create(
            name='survey name', description='survey descrpition')
        batch_obj = Batch.objects.create(
            order=1, name="Batch A", survey=survey_obj)

        
        list_1 = ListingTemplate.objects.create(name="List A9")
        qset = QuestionSet.get(pk=list_1.id)
        response = self.client.get(reverse('add_qset_subquestion_page', kwargs={"batch_id" : qset.id}))
        self.assertIn(response.status_code,[200,302])

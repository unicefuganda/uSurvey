from django.test.client import Client
from django.contrib.auth.models import User
from survey.models.batch import Batch
from survey.models import QuestionModule, Survey
from survey.models.questions import Question
from survey.models.questions import QuestionFlow

from survey.tests.base_test import BaseTest
from survey.forms.filters import DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE


class QuestionsViews(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')
        
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

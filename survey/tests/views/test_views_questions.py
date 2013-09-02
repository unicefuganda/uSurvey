from survey.tests.base_test import BaseTest
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from rapidsms.contrib.locations.models import Location, LocationType
from django.contrib import messages
from mock import patch

from survey.models import *
from survey.forms.question import QuestionForm


class QuestionsViews(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')

        self.batch = Batch.objects.create(order = 1, name = "Batch A")
        self.question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?",
                                            answer_type=Question.NUMBER, order=1)
        self.question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?",
                                            answer_type=Question.NUMBER, order=2)

    def test_get_index(self):
        response = self.client.get('/batches/%d/questions/'%self.batch.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('questions/index.html', templates)
        self.assertIn(self.question_1, response.context['questions'])
        self.assertIn(self.question_2, response.context['questions'])
        self.assertEqual(self.question_2.batch, response.context['batch'])
        self.assertIsNotNone(response.context['request'])

    @patch('django.contrib.messages.error')
    def test_no_questions_in_batch(self, mock_error):
        other_batch = Batch.objects.create(order=2, name="Other Batch")
        response = self.client.get('/batches/%d/questions/'%other_batch.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('questions/index.html', templates)
        self.assertEquals(0, len(response.context['questions']))
        self.assertEqual(other_batch, response.context['batch'])
        self.assertIsNotNone(response.context['request'])
        mock_error.assert_called_once_with(response.context['request'], 'There are no questions associated with this batch yet.')


    def test_add_new_question(self):
        response = self.client.get('/batches/%d/questions/new/'%self.batch.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('questions/new.html', templates)
        self.assertIsInstance(response.context['questionform'], QuestionForm)

    def test_question_form_is_in_response_request_context(self):
        response = self.client.get('/batches/%d/questions/new/'%self.batch.id)
        self.assertIsInstance(response.context['questionform'], QuestionForm)
        self.assertEqual(response.context['button_label'], 'Save')
        self.assertEqual(response.context['id'], 'add-question-form')
        
    def test_restricted_permissions(self):
        self.assert_restricted_permission_for("/batches/%d/questions/new/"%self.batch.id)
        self.assert_restricted_permission_for('/batches/%d/questions/'%self.batch.id)
        
    @patch('django.contrib.messages.success')
    def test_create_question_success(self, mock_success):
        form_data={
                    'text': 'This is a Question',
                    'answer_type': Question.NUMBER
        }
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)
        response = self.client.post('/batches/%d/questions/new/'%self.batch.id, data=form_data)
        question = Question.objects.filter(text=form_data['text'])
        self.failUnless(question)
        self.assertEqual(question[0].batch,self.batch)
        self.assertRedirects(response, expected_url='/batches/%d/questions/'%self.batch.id, status_code=302, target_status_code=200)
        assert mock_success.called

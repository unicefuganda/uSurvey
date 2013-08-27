from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from rapidsms.contrib.locations.models import Location, LocationType
from django.contrib import messages
from mock import patch

from survey.models import *
from survey.forms.batch import BatchForm


class QuestionsViews(TestCase):

    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_batches', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)

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



from django.test.client import Client
from mock import patch
from django.contrib.auth.models import User
from survey.models.surveys import Survey
from survey.forms.surveys import SurveyForm
from survey.tests.base_test import BaseTest

class SurveyViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')

        self.client.login(username='Rajni', password='I_Rock')
        self.form_data = {
                'name': 'survey rajni',
                'description': 'survey description rajni',
                'sample_size': 10,
                'type': True,
                }


    def test_view_survey_list(self):
        survey_1 = Survey.objects.create(name="survey A")
        survey_2 = Survey.objects.create(name="survey B")
        response = self.client.get('/surveys/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('surveys/index.html', templates)
        self.assertIn(survey_1, response.context['surveys'])
        self.assertIn(survey_2, response.context['surveys'])
        self.assertIsNotNone(response.context['request'])
        self.assertIsInstance(response.context['survey_form'], SurveyForm)


    def test_add_survey(self):
        response = self.client.get('/surveys/new/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('surveys/new.html', templates)
        self.assertIsInstance(response.context['survey_form'], SurveyForm)
        self.assertIn('add-survey-form', response.context['id'])
        self.assertIn('Save', response.context['button_label'])
        self.assertIn('New Survey', response.context['title'])
        self.assertIn('/surveys/new/', response.context['action'])

    def test_new_should_create_survey_on_post(self):
        form_data = self.form_data

        all_surveys = Survey.objects.filter(**form_data)
        self.failIf(all_surveys)
        response = self.client.post('/surveys/new/', data=form_data)
        self.assertRedirects(response, expected_url='/surveys/', status_code=302, target_status_code=200,
                             msg_prefix='')
        retrieved_surveys= Survey.objects.filter(**form_data)
        self.assertEquals(1, len(retrieved_surveys))
        self.assertIn('Survey successfully added.', response.cookies['messages'].__str__())

    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/groups/new/')
        self.assert_restricted_permission_for('/groups/')


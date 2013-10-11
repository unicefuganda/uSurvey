from django.contrib.auth.models import User
from django.test import Client
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import QuestionModule
from survey.tests.base_test import BaseTest


class QuestionModuleViewTest(BaseTest):

    def setUp(self):
        self.client = Client()

    def test_get_new_question_module(self):
        response = self.client.get('/modules/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('question_module/new.html', templates)
        self.assertIsNotNone(response.context['question_module_form'])
        self.assertIsInstance(response.context['question_module_form'], QuestionModuleForm)

    def test_post_question_module_form_ceates_question_module_and_returns_success(self):
        form_data = {'name': 'Education'}
        self.failIf(QuestionModule.objects.filter(**form_data))
        response = self.client.post('/modules/new/', data=form_data)
        self.failUnless(QuestionModule.objects.filter(**form_data))
        self.assertRedirects(response, "/modules/", 302, 200)
        success_message = "Question module successfully created."
        self.assertIn(success_message, response.cookies['messages'].value)

    def test_get_question_module_index(self):
        health_module = QuestionModule.objects.create(name="Health")
        education_module = QuestionModule.objects.create(name="Education")
        response = self.client.get('/modules/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('question_module/index.html', templates)
        self.assertIn(health_module, response.context['question_modules'])
        self.assertIn(education_module, response.context['question_modules'])

    def test_post_question_module_returns_error_message_if_similar_module_exists(self):
        QuestionModule.objects.create(name="Education")
        form_data = {'name': 'Education'}
        response = self.client.post('/modules/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('question_module/new.html', templates)
        error_message = "Question module was not created."
        self.assertIn(error_message, response.cookies['messages'].value)
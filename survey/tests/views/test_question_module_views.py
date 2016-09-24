from django.contrib.auth.models import User
from django.test import Client
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import QuestionModule, Question, HouseholdMemberGroup
from survey.models.batch import *
from survey.tests.base_test import BaseTest


class QuestionModuleViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')
        self.client.login(username='Rajni', password='I_Rock')

    def test_get_new_question_module(self):
        response = self.client.get('/modules/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('question_module/new.html', templates)
        self.assertIsNotNone(response.context['question_module_form'])
        self.assertIsInstance(
            response.context['question_module_form'], QuestionModuleForm)
        self.assertEqual(response.context['title'], "New Module")
        self.assertEqual(response.context['button_label'], "Create")
        self.assertEqual(response.context['action'], "/modules/new/")

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

    def test_get_edit_question_module(self):
        education_module = QuestionModule.objects.create(name="Education")
        response = self.client.get('/modules/%s/edit/' % education_module.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('question_module/new.html', templates)
        self.assertIsNotNone(response.context['question_module_form'])
        self.assertIsInstance(
            response.context['question_module_form'], QuestionModuleForm)
        self.assertEqual(response.context[
                         'question_module_form'].instance, education_module)
        self.assertEqual(response.context['title'], "Edit Module")
        self.assertEqual(response.context['button_label'], "Save")
        self.assertEqual(response.context[
                         'action'], "/modules/%s/edit/" % education_module.id)

    def test_post_edit_question_module(self):
        education_module = QuestionModule.objects.create(name="Eductaion")
        education_module_form = {'name': 'Education'}
        response = self.client.post(
            '/modules/%s/edit/' % education_module.id, data=education_module_form)
        self.failUnless(QuestionModule.objects.filter(
            id=education_module.id, **education_module_form))
        self.assertRedirects(response, "/modules/", 302, 200)
        success_message = "Question module successfully edited."
        self.assertIn(success_message, response.cookies['messages'].value)

    def test_delete_question_module(self):
        QuestionModule.objects.create(name="Health")
        education_module = QuestionModule.objects.create(name="Education")
        response = self.client.get('/modules/%s/delete/' % education_module.id)
        self.failIf(QuestionModule.objects.filter(id=education_module.id))
        self.assertRedirects(response, "/modules/", 302, 200)
        error_message = "Module successfully deleted."
        self.assertIn(error_message, response.cookies['messages'].value)

    def test_delete_question_module_does_not_delete_associated_questions(self):
        education_module = QuestionModule.objects.create(name="Education")
        batch = Batch.objects.create(
            name="Batch name", description='description')
        group_3 = HouseholdMemberGroup.objects.create(name="Group 3", order=2)
        question = Question.objects.create(identifier='1.1', text="This is a question1", answer_type='Numerical Answer',
                                           group=group_3, batch=batch, module=education_module)
        self.failUnless(Question.objects.filter(id=question.id))
        response = self.client.get('/modules/%s/delete/' % education_module.id)
        self.failIf(QuestionModule.objects.filter(id=education_module.id))
        self.assertRedirects(response, "/modules/", 302, 200)

    def test_delete_question_module_returns_error_if_module_does_not_exist(self):
        some_none_existing_module_id = 999999
        response = self.client.get(
            '/modules/%s/delete/' % some_none_existing_module_id)
        self.assertRedirects(response, "/modules/", 302, 200)
        error_message = "Module does not exist."
        self.assertIn(error_message, response.cookies['messages'].value)

    def test_post_question_module_returns_error_message_if_similar_module_exists(self):
        QuestionModule.objects.create(name="Education")
        form_data = {'name': 'Education'}
        response = self.client.post('/modules/new/', data=form_data)

        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('question_module/new.html', templates)
        error_message = "Question module was not created."
        self.assertIn(error_message, str(response))

    def test_permission_for_question_modules(self):
        self.assert_restricted_permission_for('/modules/')
        self.assert_restricted_permission_for('/modules/new/')
        self.assert_restricted_permission_for('/modules/1/edit/')
        self.assert_restricted_permission_for('/modules/1/delete/')

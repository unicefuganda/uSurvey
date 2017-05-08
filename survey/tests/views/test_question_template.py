from django.test.client import Client
from django.contrib.auth.models import User
from survey.models.batch import Batch
from survey.models import QuestionTemplate, Survey, QuestionModule, Batch

from survey.tests.base_test import BaseTest


class QuestionsTemplateViews(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')
        self.module = QuestionModule.objects.create(name="Education")
        self.question_1 = QuestionTemplate.objects.create(module=self.module,variable_name='a',text='ttt',answer_type='Numerical Answer')

    def test_index(self):
        response = self.client.get(reverse('show_question_library'))
        self.failUnlessEqual(response.status_code, 200)

    def test_export(self):
        response = self.client.get(reverse('export_question_library'))
        self.failUnlessEqual(response.status_code, 200)

    def test_add(self):
        data = { 'text': [self.question_1.text],
                'module': [self.module.id], 'answer_type': ['Numerical Answer']}
        response = self.client.post(reverse('new_question_library'), data=data)
        self.failUnlessEqual(response.status_code, 200)

    def test_filter(self):
        response = self.client.get(reverse('filter_question_list'))
        self.failUnlessEqual(response.status_code, 200)

    def test_qt_does_not_exist(self):
        message = "Question Template does not exist."
        self.assert_object_does_not_exist(reverse('edit_question_library',kwargs={"question_id":500}), message)

    def test_should_throw_error_if_deleting_non_existing_qt(self):
        message = "Question Template does not exist."
        self.assert_object_does_not_exist(reverse('delete_question_library',kwargs={"question_id":500}), message)

from django.test.client import Client
from django.contrib.auth.models import User
from survey.models.batch import Batch
from django.core.urlresolvers import reverse
from survey.models import (QuestionModule, Interviewer,  EnumerationArea, QuestionTemplate, NumericalAnswer,
                           TextAnswer, MultiChoiceAnswer, DateAnswer, QuestionOption, Interview, ListingTemplate,
                           ODKAccess, Question, QuestionSet,Batch, ResponseValidation, Survey)
from survey.models import QuestionTemplate, Survey, QuestionModule, Batch, ResponseValidation
from survey.tests.base_test import BaseTest

class QuestionsTemplateViewsTest(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='demo9@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('demo9', 'demo9@kant.com', 'demo9'),
                                        'can_view_batches')
        self.client.login(username='demo9', password='demo9')
        self.rsp = ResponseValidation.objects.create(validation_test="validation",constraint_message="msg")
        self.module = QuestionModule.objects.create(name="Education",description="bla blaaa")
        self.question_1 = QuestionTemplate.objects.create(module_id=self.module.id,identifier='1.1',text='ttt',answer_type='Numerical Answer',response_validation_id=1)

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

    # def test_qt_does_not_exist(self):
    #     message = "Question Template does not exist."
    #     self.assert_object_does_not_exist(reverse('edit_question_library',kwargs={"question_id":500}), message)

    def test_should_throw_error_if_deleting_non_existing_qt(self):
        message = "Question Template does not exist."
        self.assert_object_does_not_exist(reverse('delete_question_library',kwargs={"question_id":500}), message)
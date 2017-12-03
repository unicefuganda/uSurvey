from model_mommy import mommy
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
        url = reverse('new_question_library')
        response = self.client.get(url)
        self.assertIn('questionform', response.context)
        data = {'text': 'lib test text', 'identifier': 'test_identifier',
                'module': self.module.id, 'answer_type': 'Numerical Answer'}
        response = self.client.post(url, data=data)
        self.failUnlessEqual(response.status_code, 302)
        template = QuestionTemplate.objects.filter(text=data['text']).first()
        self.assertTrue(QuestionTemplate.objects.filter(text=data['text']).exists())
        created_question = QuestionTemplate.objects.filter(text=data['text']).first()
        url = reverse('edit_%s' % QuestionTemplate.resolve_tag(), args=(template.id, ))
        data['text'] = 'edited entry'
        response = self.client.post(url, data=data)
        self.assertTrue(QuestionTemplate.objects.filter(text=data['text']).count(), 1)

    def test_delete_template_question(self):
        question = mommy.make(QuestionTemplate)
        url = reverse('delete_question_template_page', args=(question.id, ))
        response = self.client.get(url)
        self.assertFalse(QuestionTemplate.objects.filter(id=question.id).exists())

    def test_filter(self):
        response = self.client.get(reverse('filter_question_list'))
        self.failUnlessEqual(response.status_code, 200)

    # def test_qt_does_not_exist(self):
    #     message = "Question Template does not exist."
    #     self.assert_object_does_not_exist(reverse('edit_question_library',kwargs={"question_id":500}), message)

    # def test_should_throw_error_if_deleting_non_existing_qt(self):
    #     message = "Question Template does not exist."
    #     self.assert_object_does_not_exist(reverse('delete_question_library',kwargs={"question_id":500}), message)
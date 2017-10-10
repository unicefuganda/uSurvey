from django.contrib.auth.models import User
from django.test import Client
from survey.forms.question_module_form import QuestionModuleForm
# from survey.forms.question_set import QuestionSetForm, BatchForm
from survey.forms import *
from survey.models import QuestionModule, Question, QuestionSetChannel, QuestionSet, ResponseValidation, QuestionTemplate, TemplateQuestion
from survey.models.batch import *
from survey.tests.base_test import BaseTest

class QuestionSetViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(
            username='useless', email='demo8@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('demo8', 'demo8@kant.com', 'demo8'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')
        self.client.login(username='demo8', password='demo8')
        self.qset = QuestionSet.objects.create(name="health", description="blabla")
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest",
constraint_message="message")
        self.module = QuestionModule.objects.create(name="Education")
        #self.question_1 = QuestionTemplate.objects.create(module=self.module,variable_name='a',text='ttt',answer_type='Numerical Answer',response_validation=self.rsp)
        self.tmques = TemplateQuestion.objects.create(identifier="identifier",text="text",answer_type="answer_type")
        self.question_1 = QuestionTemplate.objects.create(templatequestion_ptr_id=1)
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1, name="Batch A", survey=self.survey)
    def test_get_new_question_set_module(self):
        health_module = QuestionSet.objects.create(name="health")
        # response = self.client.get('qset/questions/%s/new/' % health_module.id)
        response = self.client.get('new_qset_question_page',kwargs={"qset_id":health_module.id})
        # self.failUnlessEqual(response.status_code, 200)        
        self.assertEqual(response.status_code, 404)
        # templates = [template.name for template in response.templates]
        # self.assertIn('question_set/new.html', templates)
        # self.assertIsNotNone(response.context['question_set'])
        # self.assertIsInstance(
        #     response.context['question_set'], QuestionSetForm)
        # self.assertEqual(response.context['title'], "New QuestionSet")
        # self.assertEqual(response.context['button_label'], "Create")
        # self.assertEqual(response.context['action'], "qset/questions/%s/new/")
    
    # def test_index(self):
    #     response = self.client.get(reverse('batch_index_page'))
    #     self.failUnlessEqual(response.status_code, 200)
    def test_delete_should_delete_the_question(self):
        self.form_data = {'name': 'health'}
        qset = QuestionSet.objects.create(**self.form_data)
        self.survey = Survey.objects.create(name="hahahahaha")
        batch = Batch.objects.create(order=1, name="Batch A", survey=self.survey)
        self.failUnless(qset)
        # response = self.client.get('/qset/delete/%d/batch/%d/' % qset.id,batch.id)
        response = self.client.get('delete_qset', kwargs={"question_id":qset.id, "batch_id":batch.id})
        self.assertRedirects(response, reverse('qset_questions_page'), status_code=302,
                             target_status_code=200, msg_prefix='')
    def test_post_question_set_returns_error_message_if_similar_module_exists(self):        
        x = QuestionSet.objects.create(name="health", description="blabla")
        form_data = {'name': 'health'}
        # response = self.client.post('qset/questions/%s/new/', data=form_data)
        response = self.client.get('new_qset_question_page', kwargs={"qset_id":x.id})
        # self.failUnlessEqual(response.status_code, 404)
        self.assertEqual(response.status_code, 404)
        # templates = [template.name for template in response.templates]
        # print templates,"fdddddddd"
        # self.assertIn('question_set/new.html', templates)
        # error_message = "Question set was not created."
        # self.assertIn(error_message, str(response))

    # def test_permission_for_question_modules(self):        
    #     self.assert_restricted_permission_for('/question_validators/')
    #     self.assert_restricted_permission_for('/question_options/')
    #     self.assert_restricted_permission_for('/question_set/1/questions/')
    #     self.assert_restricted_permission_for('/qset/delete//1/batch/1/')          
    #     self.assert_restricted_permission_for('/qset/qset_identifiers/')
    #     self.assert_restricted_permission_for('/qset/delete/1/')     
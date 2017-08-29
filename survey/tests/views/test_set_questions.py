from django.contrib.auth.models import User
from django.test import Client
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import QuestionModule, Question, QuestionSetChannel, QuestionSet
from survey.models.batch import *
from survey.tests.base_test import BaseTest

class SetQuestionViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(
            username='useless', email='demo8@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('demo8', 'demo8@kant.com', 'demo8'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')
        self.client.login(username='demo8', password='demo8')
        self.qset = QuestionSet.objects.create(name="health", description="blabla")
        self.module = QuestionModule.objects.create(name="Education")
        self.question_1 = QuestionTemplate.objects.create(module=self.module,variable_name='a',text='ttt',answer_type='Numerical Answer')
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1, name="Batch A", survey=self.survey)
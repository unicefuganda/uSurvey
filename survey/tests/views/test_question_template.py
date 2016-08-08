import json
from django.test.client import Client
from django.contrib.auth.models import User
from mock import patch
from survey.models.locations import *
from survey.forms.logic import LogicForm
from survey.forms.filters import QuestionFilterForm
from survey.models.batch import Batch
from survey.models import QuestionModule, Survey
from survey.models.questions import Question, QuestionOption, QuestionFlow

from survey.tests.base_test import BaseTest
from survey.forms.question import QuestionForm
from survey.forms.filters import MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE, DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE
from survey.models.householdgroups import HouseholdMemberGroup

class QuestionsTemplateViews(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')
        self.household_member_group = HouseholdMemberGroup.objects.create(name='Age 4-5', order=1)
        self.module = QuestionModule.objects.create(name="Education")
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1, name="Batch A", survey=self.survey)
        self.question_1 = Question.objects.create(identifier='1.1',text="This is a question1", answer_type='Numerical Answer',
                                            group=self.household_member_group,batch=self.batch,module=self.module)
        self.question_2 = Question.objects.create(identifier='1.2',text="This is a question2", answer_type='Numerical Answer',
                                            group=self.household_member_group,batch=self.batch,module=self.module)

    def test_index(self):
        response = self.client.get('/question_library/')
        self.failUnlessEqual(response.status_code, 200)

    def test_export(self):
        response = self.client.get('/question_library/export/')
        self.failUnlessEqual(response.status_code, 200)

    def test_add(self):
        data={'group': [self.household_member_group.id], 'text': [self.question_1.text],
              'module': [self.module.id], 'answer_type': ['Numerical Answer']}
        response = self.client.post('/question_library/new/',data=data)
        self.failUnlessEqual(response.status_code, 200)

    def test_filter(self):
        response = self.client.get('/question_library/json_filter/')
        self.failUnlessEqual(response.status_code, 200)
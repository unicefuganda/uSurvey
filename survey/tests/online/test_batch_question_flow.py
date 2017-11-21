import json
import redis
from model_mommy import mommy
from django.core.cache import cache
from django.conf import settings
from copy import deepcopy
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from survey.models import (Batch, Survey, NumericalAnswer, TextAnswer, DateAnswer, MultiChoiceAnswer, ODKAccess,
                           RespondentGroup, ParameterTemplate, EnumerationArea, Interviewer, SurveyAllocation,
                           BatchQuestion, ParameterQuestion)
from survey.models.surveys import Survey
from survey.models.questions import Question, QuestionFlow
from survey.tests.base_test import BaseTest
from survey.forms.batch import BatchForm
from survey.forms.answer import SurveyAllocationForm, AddMoreLoopForm
from survey.tests.models.survey_base_test import SurveyBaseTest


class OnlineFlowsTest(BaseTest):
    fixtures = ['enumeration_area', 'locations', 'location_types']

    def setUp(self):
        self.client = Client()
        self.survey = mommy.make(Survey)
        self.batch_data = {'name': 'test-batch', 'access_channels': [ODKAccess.choice_name(), ],
                           'survey': self.survey.id}
        self.questions_data = []
        # create a inline flows for this listing
        for answer_class in [NumericalAnswer, TextAnswer, DateAnswer, MultiChoiceAnswer]:
            self.questions_data.append({'text': 'text: %s' % answer_class.choice_name(),
                                        'answer_type': answer_class.choice_name(),
                                        'identifier': 'id_%s' % answer_class.choice_name().replace(' ', '_')})
        self.questions_data[-1]['options'] = ['Yes', 'No']
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.client.login(username='demo12', password='demo12')

    def test_add_batch(self):
        show_batch_page_url = reverse('batch_index_page', args=(self.survey.pk, ))
        response = self.client.get(show_batch_page_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Batch.objects.count(), 0)
        create_batch_url = reverse('new_batch_page', args=(self.survey.pk, ))
        response = self.client.post(create_batch_url, data=self.batch_data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Batch.objects.count(), 1)

    def test_create_group(self):
        group_params = {'text': 'age 1', 'answer_type': NumericalAnswer.choice_name(), 'identifier': 'age'}
        # check if you can reach the show params to add one
        show_param_url = reverse('show_%s' % ParameterTemplate.resolve_tag())
        response = self.client.post(show_param_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(ParameterTemplate.objects.count(), 0)
        create_params_url = reverse('new_%s' % ParameterTemplate.resolve_tag())
        response = self.client.post(create_params_url, data=group_params)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(ParameterTemplate.objects.count(), 1)
        # check if grou
        group_params = {'text': 'Choose', 'answer_type': MultiChoiceAnswer.choice_name(), 'identifier': 'choice',
                        'options': ['Yes', 'No']}
        # check if you can reach the show params to add one
        response = self.client.post(create_params_url, data=group_params)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(ParameterTemplate.objects.count(), 2)
        show_groups_url = reverse('respondent_groups_page')
        response = self.client.get(show_groups_url)
        self.assertEquals(response.status_code, 302)    # only users with 'auth.can_view_household_groups' can access
        self.assign_permission_to(User.objects.create_user('user1', 'user@kant1.com', 'demo123'),
                                  'can_view_household_groups')
        client = Client()
        client.login(username='user1', password='demo123')
        response = client.get(show_groups_url)
        self.assertEquals(response.status_code, 200)
        create_group_url = reverse('new_respondent_groups_page')
        group_data = {'name': 'group1', 'description': 'etc',
                      'test_question': ParameterTemplate.objects.order_by('created').first().id,
                      'validation_test': 'between', 'min': 3, 'max': 5}
        response = client.post(create_group_url, data=group_data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(RespondentGroup.objects.count(), 1)
        group = RespondentGroup.objects.first()
        edit_group_url = reverse('respondent_groups_edit', args=(group.id, ))
        self.assertIn(edit_group_url, response.url)
        group_data = {'name': 'group1', 'description': 'etc', 'validation_test': 'equals',
                      'test_question': ParameterTemplate.objects.order_by('created').last().id,
                      'value': 1}
        response = client.post(edit_group_url, data=group_data)        #just post to same url
        self.assertEquals(RespondentGroup.objects.first().group_conditions.count(), 2)
        self.assertEquals(response.status_code, 302)
        self.assertIn(edit_group_url, response.url)

    def test_add_questions_to_batch(self):
        self.test_add_batch()
        self.test_create_group()
        batch = Batch.objects.first()
        group = RespondentGroup.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(batch.pk, ))
        i = 0
        question_data = self.questions_data
        question_data[1]['group'] = group.id
        question_data[3]['group'] = group.id
        for idx, data in enumerate(question_data):
            data['qset'] = batch.pk
            response = self.client.post(create_sq_url, data=data)
            self.assertEquals(len(batch.flow_questions), idx+1),
            question = batch.flow_questions[-1]
            self.assertEquals(question.text, data['text'])
            self.assertEquals(question.identifier, data['identifier'])
            self.assertEquals(question.answer_type, data['answer_type'])
            self.assertEquals(question.qset.pk, batch.pk)
            if 'group' in data:
                self.assertEquals(question.group.id, data['group'])
        # now check that the first batch question is parameter first.
        first_param = ParameterQuestion.objects.order_by('created').first().pk
        self.assertEquals(batch.g_first_question.pk, first_param)
        last_param = ParameterQuestion.objects.order_by('created').last()
        self.assertEquals(batch.all_questions[1].pk, last_param.pk)
        self.assertEquals(len(batch.all_questions), ParameterQuestion.objects.count() + BatchQuestion.objects.count())



# class USSDFlowTest(SurveyBaseTest):
#
#     def setUp(self):
#         super(USSDFlowTest, self).setUp()
#         ussd_url = reverse('ussd')


import json
import redis
from model_mommy import mommy
from django.core.cache import cache
from django.conf import settings
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from survey.models import (QuestionModule, Interviewer,  EnumerationArea, QuestionTemplate, NumericalAnswer,
                           TextAnswer, MultiChoiceAnswer, DateAnswer, QuestionOption, Interview, ListingTemplate,
                           Question, ODKAccess, Answer)
from survey.models.surveys import Survey
from survey.models.questions import Question, QuestionFlow
from survey.tests.base_test import BaseTest
from survey.forms.batch import BatchForm


class OnlineFlowsTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.listing_data = {'name': 'test-listing', 'access_channels': [ODKAccess.choice_name(), ], }
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

    def test_add_listing(self):
        create_qset_url = reverse('new_%s_page' % ListingTemplate.resolve_tag())
        response = self.client.post(create_qset_url, data=self.listing_data)
        self.assertEquals(ListingTemplate.objects.count(), 1)
        self.assertEquals(ListingTemplate.objects.first().name, self.listing_data['name'])

    def test_add_question_to_listing(self):
        self.test_add_listing()
        listing = ListingTemplate.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(listing.pk, ))
        for data in self.questions_data:
            data['qset'] = listing.pk
            response = self.client.post(create_sq_url, data=data)
            question = Question.objects.order_by('created').last()
            self.assertEquals(question.text, data['text'])
            self.assertEquals(question.identifier, data['identifier'])
            self.assertEquals(question.answer_type, data['answer_type'])
            self.assertEquals(question.qset.pk, listing.pk)

    def test_first_question_text_comes_correctly(self):
        self.test_add_question_to_listing()
        listing = ListingTemplate.objects.first()
        qflow_url = reverse('test_qset_flow', args=(listing.pk, ))
        response = self.client.get(qflow_url, data={'format': 'text'})
        self.assertIn(listing.start_question.text, response.content)

    def test_question_follows_flow_for_inline_questions(self):
        self.test_add_question_to_listing()
        listing = ListingTemplate.objects.first()
        questions = Question.objects.order_by('created')
        # confirm the order of creation questions
        for idx, flow_question in enumerate(listing.flow_questions):
            self.assertEqual(flow_question.pk, questions[idx].pk)
        inlines = listing.questions_inline()
        # confirm question flow is same as inlines for pure add question at end of flow
        for idx, flow_question in enumerate(inlines):
            self.assertEqual(flow_question.pk, questions[idx].pk)

    def test_question_response_flows(self):
        self.test_first_question_text_comes_correctly()
        listing = ListingTemplate.objects.first()
        qflow_url = reverse('test_qset_flow', args=(listing.pk, ))
        inlines = listing.questions_inline()
        # first is numeric
        # questions saved like this [NumericalAnswer, TextAnswer, DateAnswer, MultiChoiceAnswer]
        response = self.client.get(qflow_url, data={'value': 1, 'format': 'text'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[1].text, response.content)
        # second question is text
        response = self.client.post(qflow_url, data={'value': 'good', 'format': 'text'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[2].text, response.content)
        # third question is date
        response = self.client.post(qflow_url, data={'value': '2-10-2017', 'format': 'text'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[3].text, response.content)
        # fourth question is multichoice
        response = self.client.post(qflow_url, data={'value': 'yes', 'format': 'text'})
        self.assertEqual(response.status_code, 200)

    def test_



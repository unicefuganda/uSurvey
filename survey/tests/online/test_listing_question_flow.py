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
                           Question, ODKAccess, Answer, SurveyAllocation, QuestionLoop, ParameterTemplate,
                           RespondentGroup)
from survey.models.surveys import Survey
from survey.models.questions import Question, QuestionFlow
from survey.tests.base_test import BaseTest
from survey.forms.question_set import BatchForm
from survey.forms.answer import SurveyAllocationForm, AddMoreLoopForm


class OnlineFlowsTest(BaseTest):
    fixtures = ['enumeration_area', 'locations', 'location_types']

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
        response = self.client.post(qflow_url, data={'value': 1, 'format': 'text'})
        self.assertEqual(response.status_code, 200)

    def test_interviewer_gets_correct_survey(self):
        self.test_add_question_to_listing()
        listing = ListingTemplate.objects.first()
        survey = mommy.make(Survey, listing_form=listing)
        create_interviewer_url = reverse('new_interviewer_page')
        eas = EnumerationArea.objects.all()[:2]
        odk_token = 'odk-pass'
        odk_id = 'odk-user'
        interviewer_data = {'name': 'Test interviewer', 'date_of_birth': '17-07-1981',
                            'ea': eas.values_list('id', flat=True), 'survey': survey.id,
                            'odk_token': odk_token, 'user_identifier': odk_id, 'ussd_access-TOTAL_FORMS': 0,
                            'ussd_access-INITIAL_FORMS': 0, 'ussd_access-MIN_NUM_FORMS': 0,
                            'ussd_access-MAX_NUM_FORMS': 0, 'gender': Interviewer.MALE,
                            'level_of_education': Interviewer.LEVEL_OF_EDUCATION_CHOICES[0][0],
                            'language': Interviewer.LANGUAGES_CHOICES[0][0]}
        demo = self.assign_permission_to(User.objects.create_user('demo123', 'demo12@kant1.com', 'demo123'),
                                         'can_view_interviewers')
        client = Client()
        client.login(username='demo123', password='demo123')
        response = client.post(create_interviewer_url, data=interviewer_data)
        self.assertEquals(Interviewer.objects.count(), 1)
        # check if a survey allocation was created
        self.assertEquals(SurveyAllocation.objects.count(), len(eas))       # equal no of allocations created
        survey_allocation = SurveyAllocation.objects.first()
        self.assertEquals(survey_allocation.interviewer.name, interviewer_data['name'])
        self.assertEquals(survey_allocation.survey.id, interviewer_data['survey'])
        interviewer_online_flow_url = reverse('online_interviewer_view')
        answer_data = {'uid': odk_id, 'format': 'text'}
        response = client.get(interviewer_online_flow_url, data=answer_data)
        # check that the interviewer is asked to select EA first
        self.assertIn('answer_form', response.context)
        self.assertEquals(response.context['answer_form'].__class__, SurveyAllocationForm)
        # now select the allocation form
        answer_data['value'] = survey_allocation.id
        inlines = listing.questions_inline()
        response = client.get(interviewer_online_flow_url, data=answer_data)
        self.assertEquals(response.status_code, 200)
        self.assertIn(inlines[0].text, response.content)
        answer_data['value'] = 1
        response = self.client.get(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[1].text, response.content)
        # second question is text
        answer_data['value'] = 'good'
        response = self.client.post(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[2].text, response.content)
        # third question is date
        answer_data['value'] = '2-10-2017'
        response = self.client.post(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[3].text, response.content)
        # fourth question is multichoice
        answer_data['value'] = 1        # multi choice selects question order
        del answer_data['format']
        response = self.client.post(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.context['template_file'], "interviews/completed.html")

    def test_looping_list(self):
        # create listing and questions
        self.test_add_question_to_listing()
        listing = ListingTemplate.objects.first()
        survey = mommy.make(Survey, listing_form=listing)
        inlines = listing.questions_inline()
        manage_loop_url = reverse('loop_qset_question_page', args=(inlines[1].pk, ))
        response = self.client.get(manage_loop_url)
        self.assertEquals(response.status_code, 200)
        # create basic user defined loop from second question to last
        loop_data = {'loop_starter': inlines[1].pk, 'loop_ender': inlines[2].pk, }
        response = self.client.post(manage_loop_url, data=loop_data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(QuestionLoop.objects.count(), 1)
        loop = QuestionLoop.objects.first()
        self.assertEquals(loop.loop_starter, inlines[1])
        self.assertEquals(loop.loop_ender, inlines[2])
        create_interviewer_url = reverse('new_interviewer_page')
        eas = EnumerationArea.objects.all()[:2]
        odk_token = 'odk-pass'
        odk_id = 'odk-user'
        interviewer_data = {'name': 'Test interviewer', 'date_of_birth': '17-07-1981',
                            'ea': eas.values_list('id', flat=True), 'survey': survey.id,
                            'odk_token': odk_token, 'user_identifier': odk_id, 'ussd_access-TOTAL_FORMS': 0,
                            'ussd_access-INITIAL_FORMS': 0, 'ussd_access-MIN_NUM_FORMS': 0,
                            'ussd_access-MAX_NUM_FORMS': 0, 'gender': Interviewer.MALE,
                            'level_of_education': Interviewer.LEVEL_OF_EDUCATION_CHOICES[0][0],
                            'language': Interviewer.LANGUAGES_CHOICES[0][0]}
        demo = self.assign_permission_to(User.objects.create_user('demo123', 'demo12@kant1.com', 'demo123'),
                                         'can_view_interviewers')
        client = Client()
        client.login(username='demo123', password='demo123')
        response = client.post(create_interviewer_url, data=interviewer_data)
        survey_allocation = SurveyAllocation.objects.first()
        interviewer = survey_allocation.interviewer
        client = self.client
        interviewer_online_flow_url = reverse('online_interviewer_view')
        answer_data = {'uid': odk_id, 'format': 'text'}
        response = client.get(interviewer_online_flow_url, data=answer_data)
        # check that the interviewer is asked to select EA first
        self.assertIn('answer_form', response.context)
        self.assertEquals(response.context['answer_form'].__class__, SurveyAllocationForm)
        # now select the allocation form
        answer_data['value'] = survey_allocation.id
        inlines = listing.questions_inline()
        response = client.get(interviewer_online_flow_url, data=answer_data)
        self.assertEquals(response.status_code, 200)
        self.assertIn(inlines[0].text, response.content)
        answer_data['value'] = 1
        response = self.client.get(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[1].text, response.content)
        # second question is text
        answer_data['value'] = 'good'
        response = self.client.post(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[2].text, response.content)
        # third question is date
        answer_data['value'] = '2-10-2017'
        response = self.client.post(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(AddMoreLoopForm.DEFAULT_LOOP_PROMPT, response.content)
        answer_data['value'] = '1'      # repeat the loop
        response = self.client.post(interviewer_online_flow_url, data=answer_data)  # should taje back to ques 1
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[1].text, response.content)
        # second question is text
        answer_data['value'] = 'good'
        response = self.client.post(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(inlines[2].text, response.content)
        # third question is date
        answer_data['value'] = '2-10-2017'
        response = self.client.post(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(AddMoreLoopForm.DEFAULT_LOOP_PROMPT, response.content)
        answer_data['value'] = '2'      # end the loop
        response = self.client.post(interviewer_online_flow_url, data=answer_data)
        # fourth question is multichoice
        self.assertIn(inlines[3].text, response.content)
        answer_data['value'] = 1        # multi choice selects question order
        del answer_data['format']
        response = self.client.post(interviewer_online_flow_url, data=answer_data)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.context['template_file'], "interviews/completed.html")

    def test_conditional_flow(self):
        pass
from django.test import TestCase
from django.test.client import Client
from rapidsms.contrib.locations.models import LocationType
from survey.models_file import *
import json
import datetime
import urllib2
from survey.views import *
from survey.ussd import *
from random import randint
from rapidsms.backends.database.models import BackendMessage


class USSDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.ussd_params = {
                                'transactionId': "123344" + str(randint(1, 99999)),
                                'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
                                'msisdn': '2567765' + str(randint(1, 99999)),
                                'ussdServiceCode': '130',
                                'ussdRequestString': '',
                                'response': "false"
                            }
        self.investigator = Investigator.objects.create(name="investigator name", mobile_number=self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, ''), location=Location.objects.create(name="Kampala"), backend = Backend.objects.create(name='something'))
        self.household = Household.objects.create(investigator=self.investigator)
        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname")
        self.household_head_1 = HouseholdHead.objects.create(household=Household.objects.create(investigator=self.investigator), surname="Name " + str(randint(1, 9999)))
        self.batch = Batch.objects.create(order = 1)
        self.batch.open_for_location(self.investigator.location)

    def reset_session(self):
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))
        self.ussd_params['response'] = 'false'
        self.ussd_params['ussdRequestString'] = ''

    def select_household(self):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"
        response = self.client.post('/ussd', data=self.ussd_params)
        self.ussd_params['ussdRequestString'] = "1"

    def test_no_households(self):
        investigator = Investigator.objects.create(name="investigator name", mobile_number="1234567890", location=self.investigator.location, backend = Backend.objects.create(name='something1'))
        self.ussd_params['msisdn'] = investigator.mobile_number
        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['NO_HOUSEHOLDS']
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_numerical_questions(self):
        question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?", answer_type=Question.NUMBER, order=2)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "4"

        response = self.client.post('/ussd', data=self.ussd_params)

        self.assertEquals(4, NumericalAnswer.objects.get(investigator=self.investigator, question=question_1).answer)

        response_string = "responseString=%s&action=request" % question_2.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(2, NumericalAnswer.objects.get(investigator=self.investigator, question=question_2).answer)

    def test_textual_questions(self):
        question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.TEXT, order=1)
        question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?", answer_type=Question.TEXT, order=2)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "Reply one"

        response = self.client.post('/ussd', data=self.ussd_params)

        self.assertEquals(self.ussd_params['ussdRequestString'], TextAnswer.objects.get(investigator=self.investigator, question=question_1).answer)

        response_string = "responseString=%s&action=request" % question_2.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['ussdRequestString'] = "Reply Two"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(self.ussd_params['ussdRequestString'], TextAnswer.objects.get(investigator=self.investigator, question=question_2).answer)

    def test_multichoice_questions(self):
        question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.MULTICHOICE, order=1)
        option_1_1 = QuestionOption.objects.create(question=question_1, text="OPTION 1", order=1)
        option_1_2 = QuestionOption.objects.create(question=question_1, text="OPTION 2", order=2)

        question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?", answer_type=Question.MULTICHOICE, order=2)
        option_2_1 = QuestionOption.objects.create(question=question_2, text="OPTION 1", order=1)
        option_2_2 = QuestionOption.objects.create(question=question_2, text="OPTION 2", order=2)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = str(option_1_1.order)

        response = self.client.post('/ussd', data=self.ussd_params)

        self.assertEquals(option_1_1, MultiChoiceAnswer.objects.get(investigator=self.investigator, question=question_1).answer)

        response_string = "responseString=%s&action=request" % question_2.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['ussdRequestString'] = str(option_2_1.order)

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(option_2_1, MultiChoiceAnswer.objects.get(investigator=self.investigator, question=question_2).answer)

    def test_multichoice_questions_pagination(self):
        question = Question.objects.create(batch=self.batch, text="This is a question", answer_type=Question.MULTICHOICE, order=1)
        option_1 = QuestionOption.objects.create(question=question, text="OPTION 1", order=1)
        option_2 = QuestionOption.objects.create(question=question, text="OPTION 2", order=2)
        option_3 = QuestionOption.objects.create(question=question, text="OPTION 3", order=3)
        option_4 = QuestionOption.objects.create(question=question, text="OPTION 4", order=4)
        option_5 = QuestionOption.objects.create(question=question, text="OPTION 5", order=5)
        option_6 = QuestionOption.objects.create(question=question, text="OPTION 6", order=6)
        option_7 = QuestionOption.objects.create(question=question, text="OPTION 7", order=7)
        back_text = Question.PREVIOUS_PAGE_TEXT
        next_text = Question.NEXT_PAGE_TEXT

        question_2 = Question.objects.create(batch=self.batch, text="This is a question", answer_type=Question.MULTICHOICE, order=2)
        option_8 = QuestionOption.objects.create(question=question_2, text="OPTION 1", order=1)
        option_9 = QuestionOption.objects.create(question=question_2, text="OPTION 2", order=2)

        self.select_household()

        page_1 = "%s\n1: %s\n2: %s\n3: %s\n%s" % (question.text, option_1.text, option_2.text, option_3.text, next_text)
        page_2 = "%s\n4: %s\n5: %s\n6: %s\n%s\n%s" % (question.text, option_4.text, option_5.text, option_6.text, back_text, next_text)
        page_3 = "%s\n7: %s\n%s" % (question.text, option_7.text, back_text)

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % page_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "#"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % page_2
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "#"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % page_3
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "*"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % page_2
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "*"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % page_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "#"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % page_2
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_2.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_reanswer_question(self):
        question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?", answer_type=Question.NUMBER, order=2)
        rule = AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['REANSWER'], condition=AnswerRule.CONDITIONS['GREATER_THAN_QUESTION'], validate_with_question=question_1)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "5"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_2.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "10"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("RECONFIRM: " + question_1.text)
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "5"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("RECONFIRM: " + question_2.text)
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_text_invalid_answer(self):
        question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.TEXT, order=1)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = ""

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + question_1.text)
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "something"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)


    def test_numerical_invalid_answer(self):
        question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        self.select_household()
        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "a"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + question_1.text)
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_multichoice_invalid_answer(self):
        question_1 = Question.objects.create(batch=self.batch, text="This is a question", answer_type=Question.MULTICHOICE, order=1)
        option_1 = QuestionOption.objects.create(question=question_1, text="OPTION 1", order=1)
        option_2 = QuestionOption.objects.create(question=question_1, text="OPTION 2", order=2)
        self.select_household()
        page_1 = "%s\n1: %s\n2: %s" % (question_1.text, option_1.text, option_2.text)

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % page_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "a"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + page_1)
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "4"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + page_1)
        self.assertEquals(urllib2.unquote(response.content), response_string)


        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_end_interview_confirmation(self):
        question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?", answer_type=Question.NUMBER, order=2)
        rule = AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'], condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.investigator = Investigator.objects.get(id=self.investigator.pk)

        self.assertEquals(len(self.investigator.get_from_cache('CONFIRM_END_INTERVIEW')), 0)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "0"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("RECONFIRM: " + question_1.text)
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(len(self.investigator.get_from_cache('CONFIRM_END_INTERVIEW')), 1)

        self.assertEquals(0, NumericalAnswer.objects.count())

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "0"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.investigator = Investigator.objects.get(id=self.investigator.pk)
        self.assertEquals(len(self.investigator.get_from_cache('CONFIRM_END_INTERVIEW')), 0)
        self.assertEquals(self.household.has_pending_survey(), False)

        self.ussd_params['response'] = "false"
        self.ussd_params['ussdRequestString'] = ""
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))

        homepage = "Welcome %s to the survey.\n00: Households list" % self.investigator.name

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % homepage
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"

        households_list_1 = "%s\n1: %s*\n2: %s" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head.surname, self.household_head_1.surname)

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_end_interview_confirmation_alternative(self):
        question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?", answer_type=Question.NUMBER, order=2)
        rule = AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'], condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "0"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("RECONFIRM: " + question_1.text)
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(0, NumericalAnswer.objects.count())

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_2.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_resume_functionality(self):
        question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?", answer_type=Question.NUMBER, order=2)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "0"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_2.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.reset_session()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_2.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        last_answered = self.investigator.last_answered()
        last_answered.created -= datetime.timedelta(minutes=USSD.TIMEOUT_MINUTES, seconds=1)
        last_answered.save()
        self.reset_session()

        homepage = "Welcome %s to the survey.\n00: Households list" % self.investigator.name

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % homepage
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"

        households_list_1 = "%s\n1: %s\n2: %s" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head.surname, self.household_head_1.surname)

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.reset_session()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % homepage
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % question_2.text
        self.assertEquals(urllib2.unquote(response.content), response_string)


class USSDTestCompleteFlow(TestCase):

    def create_household_head(self):
        return HouseholdHead.objects.create(household=Household.objects.create(investigator=self.investigator), surname="Name " + str(randint(1, 9999)))

    def setUp(self):
        self.client = Client()
        self.ussd_params = {
                                'transactionId': "123344" + str(randint(1, 99999)),
                                'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
                                'msisdn': '2567765' + str(randint(1, 99999)),
                                'ussdServiceCode': '130',
                                'ussdRequestString': '',
                                'response': "false"
                            }
        self.investigator = Investigator.objects.create(name="investigator name", mobile_number=self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, ''), location=Location.objects.create(name="Kampala"), backend = Backend.objects.create(name='something'))
        self.household_head_1 = self.create_household_head()
        self.household_head_2 = self.create_household_head()
        self.household_head_3 = self.create_household_head()
        self.household_head_4 = self.create_household_head()
        self.household_head_5 = self.create_household_head()
        self.household_head_6 = self.create_household_head()
        self.household_head_7 = self.create_household_head()
        self.household_head_8 = self.create_household_head()
        self.household_head_9 = self.create_household_head()
        self.batch = Batch.objects.create(order=1)
        self.batch_b = Batch.objects.create(order=2)
        self.batch.open_for_location(self.investigator.location)
        self.question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        self.question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?", answer_type=Question.NUMBER, order=2)
        self.question_1_b = Question.objects.create(batch=self.batch_b, text="How many members are there in this household? Batch B", answer_type=Question.NUMBER, order=1)

    def test_flow(self):
        homepage = "Welcome %s to the survey.\n00: Households list" % self.investigator.name

        self.ussd_params['ussdRequestString'] = "adassd"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % homepage
        self.assertEquals(urllib2.unquote(response.content), response_string)

        households_list_1 = "%s\n1: %s\n2: %s\n3: %s\n4: %s\n#: Next" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head_1.surname, self.household_head_2.surname, self.household_head_3.surname, self.household_head_4.surname)

        households_list_2 = "%s\n5: %s\n6: %s\n7: %s\n8: %s\n*: Back\n#: Next" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head_5.surname, self.household_head_6.surname, self.household_head_7.surname, self.household_head_8.surname)

        households_list_3 = "%s\n9: %s\n*: Back" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head_9.surname)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "#"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_2
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "#"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_3
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "*"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_2
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "*"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "100"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("INVALID SELECTION: " + households_list_1)
        self.assertEquals(urllib2.unquote(response.content), response_string)


        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "adss"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % ("INVALID SELECTION: " + households_list_1)
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "10"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_2.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(10, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_1, household=self.household_head_1.household).answer)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "5"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(5, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_2, household=self.household_head_1.household).answer)

        # Deleting all the households except 1 and 2

        self.household_head_3.household.delete()
        self.household_head_4.household.delete()
        self.household_head_5.household.delete()
        self.household_head_6.household.delete()
        self.household_head_7.household.delete()
        self.household_head_8.household.delete()
        self.household_head_9.household.delete()

        # Survey for the next household

        self.ussd_params['response'] = "false"
        self.ussd_params['ussdRequestString'] = ""
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % homepage
        self.assertEquals(urllib2.unquote(response.content), response_string)

        households_list_1 = "%s\n1: %s*\n2: %s" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head_1.surname, self.household_head_2.surname)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "10"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_2.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(10, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_1, household=self.household_head_2.household).answer)

        self.ussd_params['response'] = "false"
        self.ussd_params['ussdRequestString'] = ""
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_2.text
        self.assertEquals(urllib2.unquote(response.content), response_string)


        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "5"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(5, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_2, household=self.household_head_2.household).answer)

        # Retaking survey for an household

        self.ussd_params['response'] = "false"
        self.ussd_params['ussdRequestString'] = ""
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % homepage
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"

        households_list_1 = "%s\n1: %s*\n2: %s*" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head_1.surname, self.household_head_2.surname)

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % USSD.MESSAGES['RETAKE_SURVEY']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % USSD.MESSAGES['RETAKE_SURVEY']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "adads"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "2"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % USSD.MESSAGES['RETAKE_SURVEY']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(2, NumericalAnswer.objects.filter(investigator=self.investigator, household=self.household_head_2.household).count())

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_1.text
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(0, NumericalAnswer.objects.filter(investigator=self.investigator, household=self.household_head_2.household).count())

    def test_show_completion_star_next_to_household_head_name(self):
        self.household_head_1.household.batch_completed(self.batch)
        self.household_head_3.household.batch_completed(self.batch)
        homepage = "Welcome %s to the survey.\n00: Households list" % self.investigator.name

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % homepage
        self.assertEquals(urllib2.unquote(response.content), response_string)

        households_list_1 = "%s\n1: %s*\n2: %s\n3: %s*\n4: %s\n#: Next" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head_1.surname, self.household_head_2.surname, self.household_head_3.surname, self.household_head_4.surname)
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_retake_survey_time_limit(self):
        self.household_head_1.household.batch_completed(self.batch)
        self.investigator.answered(self.question_1, self.household_head_1.household, 1)
        self.investigator.answered(self.question_2, self.household_head_1.household, 1)

        households_list_1 = "%s\n1: %s*\n2: %s\n3: %s\n4: %s\n#: Next" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head_1.surname, self.household_head_2.surname, self.household_head_3.surname, self.household_head_4.surname)
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % USSD.MESSAGES['RETAKE_SURVEY']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        completion = HouseholdBatchCompletion.objects.filter(batch=self.batch)[0]
        completion.created -= datetime.timedelta(minutes=USSD.TIMEOUT_MINUTES, seconds=1)
        completion.save()

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['BATCH_5_MIN_TIMEDOUT_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_completed_batch_timeout_for_household_after_5_min_should_allow_other_batches(self):
        self.household_head_1.household.batch_completed(self.batch)
        self.investigator.answered(self.question_1, self.household_head_1.household, 1)
        self.investigator.answered(self.question_2, self.household_head_1.household, 1)

        completion = HouseholdBatchCompletion.objects.filter(batch=self.batch)[0]

        latest_answer = NumericalAnswer.objects.all().latest()
        latest_answer.created -= datetime.timedelta(minutes=(USSD.TIMEOUT_MINUTES+1), seconds=1)
        latest_answer.save()

        answer_one = NumericalAnswer.objects.filter(question=self.question_1)[0]
        answer_one.created -= datetime.timedelta(minutes=(USSD.TIMEOUT_MINUTES+2), seconds=1)
        answer_one.save()

        self.batch.close_for_location(self.investigator.location)
        self.batch_b.open_for_location(self.investigator.location)

        self.client.post('/ussd', data=self.ussd_params)

        households_list_1 = "%s\n1: %s\n2: %s\n3: %s\n4: %s\n#: Next" % (USSD.MESSAGES['HOUSEHOLD_LIST'],
                                                                         self.household_head_1.surname,
                                                                         self.household_head_2.surname,
                                                                         self.household_head_3.surname,
                                                                         self.household_head_4.surname)
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % households_list_1
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_1_b.text
        self.assertEquals(urllib2.unquote(response.content), response_string)


class USSDOpenBatch(TestCase):

    def setUp(self):
        self.client = Client()
        self.ussd_params = {
                                'transactionId': "123344" + str(randint(1, 99999)),
                                'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
                                'msisdn': '2567765' + str(randint(1, 99999)),
                                'ussdServiceCode': '130',
                                'ussdRequestString': '',
                                'response': "false"
                            }
        self.investigator = Investigator.objects.create(name="investigator name", mobile_number=self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, ''), location=Location.objects.create(name="Kampala"), backend = Backend.objects.create(name='something'))
        self.household = Household.objects.create(investigator=self.investigator)
        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname")
        self.household_head_1 = HouseholdHead.objects.create(household=Household.objects.create(investigator=self.investigator), surname="Name " + str(randint(1, 9999)))
        batch = Batch.objects.create(order = 1)

    def test_closed_batch(self):
        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['NO_OPEN_BATCH']
        self.assertEquals(urllib2.unquote(response.content), response_string)


class USSDWithMultipleBatches(TestCase):

    def setUp(self):
        self.client = Client()
        self.ussd_params = {
                                'transactionId': "123344" + str(randint(1, 99999)),
                                'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
                                'msisdn': '2567765' + str(randint(1, 99999)),
                                'ussdServiceCode': '130',
                                'ussdRequestString': '',
                                'response': "false"
                            }

        self.country = LocationType.objects.create(name='Country', slug='country')
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.district = LocationType.objects.create(name='District', slug='district')
        self.location = Location.objects.create(name="Kampala", type=self.district, tree_parent=self.uganda)
        self.investigator = Investigator.objects.create(name="investigator name", mobile_number=self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, ''), location=self.location, backend = Backend.objects.create(name='something'))
        self.household = Household.objects.create(investigator=self.investigator)
        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname")
        self.household_head_1 = HouseholdHead.objects.create(household=Household.objects.create(investigator=self.investigator), surname="Name " + str(randint(1, 9999)))
        self.batch = Batch.objects.create(order=1)
        self.question_1 = Question.objects.create(batch=self.batch, text="Question 1?", answer_type=Question.NUMBER, order=1)
        self.question_2 = Question.objects.create(batch=self.batch, text="Question 2?", answer_type=Question.NUMBER, order=2)
        self.batch_1 = Batch.objects.create(order=2)
        self.question_3 = Question.objects.create(batch=self.batch_1, text="Question 3?", answer_type=Question.NUMBER, order=1)
        self.question_4 = Question.objects.create(batch=self.batch_1, text="Question 4?", answer_type=Question.NUMBER, order=2)

    def select_household(self, household = 1):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"
        response = self.client.post('/ussd', data=self.ussd_params)
        self.ussd_params['ussdRequestString'] = str(household)

    def test_with_one_batch_open(self):
        self.batch.open_for_location(self.location)

        self.select_household()

        self.assertEquals(HouseholdBatchCompletion.objects.count(), 0)

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_1.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_2.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(HouseholdBatchCompletion.objects.count(), 1)
        household_completed = HouseholdBatchCompletion.objects.latest('id')
        self.assertEquals(household_completed.household, self.household)
        self.assertEquals(household_completed.investigator, self.investigator)
        self.assertEquals(household_completed.batch, self.batch)

    def test_with_two_batch_open(self):
        self.batch.open_for_location(self.location)
        self.batch_1.open_for_location(self.location)

        self.select_household()

        self.assertEquals(HouseholdBatchCompletion.objects.count(), 0)

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_1.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_2.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_3.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(HouseholdBatchCompletion.objects.count(), 1)
        household_completed = HouseholdBatchCompletion.objects.latest('id')
        self.assertEquals(household_completed.household, self.household)
        self.assertEquals(household_completed.investigator, self.investigator)
        self.assertEquals(household_completed.batch, self.batch)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_4.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.assertEquals(HouseholdBatchCompletion.objects.count(), 2)
        household_completed = HouseholdBatchCompletion.objects.latest('id')
        self.assertEquals(household_completed.household, self.household)
        self.assertEquals(household_completed.investigator, self.investigator)
        self.assertEquals(household_completed.batch, self.batch_1)

    def test_with_second_batch_open(self):
        self.batch_1.open_for_location(self.location)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_3.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_4.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_with_batch_open_for_parent_location(self):
        self.batch.open_for_location(self.uganda)

        self.select_household()

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_1.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=request" % self.question_2.to_ussd()
        self.assertEquals(urllib2.unquote(response.content), response_string)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "1"

        response = self.client.post('/ussd', data=self.ussd_params)
        response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_string)


class RandomHouseHoldSelectionTest(TestCase):
    def setUp(self):
        Backend.objects.create(name='HTTP')
        self.client = Client()
        self.ussd_params = {
            'transactionId': 123344,
            'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
            'msisdn': '256776520831',
            'ussdServiceCode': '130',
            'ussdRequestString': '',
            'response': 'false'
        }

    def test_selection(self):
        mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
        self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

        response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)
        self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = " 100 "

        response_message = "responseString=%s&action=end" % HouseHoldSelection.MESSAGES['HOUSEHOLD_SELECTION_SMS_MESSAGE']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)
        self.assertEquals(RandomHouseHoldSelection.objects.count(), 1)

        household_selection = RandomHouseHoldSelection.objects.all()[0]
        self.assertEquals(household_selection.mobile_number, mobile_number)
        self.assertEquals(household_selection.no_of_households, 100)
        selected_households = household_selection.selected_households.split(',')
        self.assertEquals(len(selected_households), 10)

        message = BackendMessage.objects.get(identity=self.ussd_params['msisdn'])
        self.assertEquals(message.text, household_selection.text_message())

    def test_selection_retry(self):
        mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
        selected_households = "hello"
        household_selection = RandomHouseHoldSelection.objects.create(mobile_number=mobile_number, no_of_households=100, selected_households=selected_households)

        response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "999"

        response_message = "responseString=%s&action=end" % HouseHoldSelection.MESSAGES['HOUSEHOLD_SELECTION_SMS_MESSAGE']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.assertEquals(urllib2.unquote(response.content), response_message)
        self.failUnlessEqual(response.status_code, 200)

        self.assertEquals(RandomHouseHoldSelection.objects.get(id=household_selection.pk).selected_households, selected_households)

    def test_less_than_ten_households_failure(self):
        mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
        self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

        response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "9"

        response = self.client.get('/ussd', data=self.ussd_params)
        response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES['HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE']
        self.assertEquals(urllib2.unquote(response.content), response_message)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "11"

        response_message = "responseString=%s&action=end" % HouseHoldSelection.MESSAGES['HOUSEHOLD_SELECTION_SMS_MESSAGE']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.assertEquals(urllib2.unquote(response.content), response_message)
        self.failUnlessEqual(response.status_code, 200)

        household_selection = RandomHouseHoldSelection.objects.all()[0]
        self.assertEquals(household_selection.mobile_number, mobile_number)
        self.assertEquals(household_selection.no_of_households, 11)
        selected_households = household_selection.selected_households.split(',')
        self.assertEquals(len(selected_households), 10)

        message = BackendMessage.objects.get(identity=self.ussd_params['msisdn'])
        self.assertEquals(message.text, household_selection.text_message())

    def test_sort_household_selection_list(self):
        mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
        self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

        response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)
        self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = " 100 "

        response_message = "responseString=%s&action=end" % HouseHoldSelection.MESSAGES['HOUSEHOLD_SELECTION_SMS_MESSAGE']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)
        self.assertEquals(RandomHouseHoldSelection.objects.count(), 1)

        household_selection = RandomHouseHoldSelection.objects.all()[0]
        self.assertEquals(household_selection.mobile_number, mobile_number)
        self.assertEquals(household_selection.no_of_households, 100)
        selected_households = household_selection.selected_households.split(',')
        selected_households = map(int,selected_households)
        self.assertEquals(len(selected_households), 10)
        self.assertEqual(sorted(selected_households), selected_households)

        message = BackendMessage.objects.get(identity=self.ussd_params['msisdn'])
        self.assertEquals(message.text, household_selection.text_message())

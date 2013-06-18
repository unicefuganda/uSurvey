from django.test import TestCase
from django.test.client import Client
from survey.models import *
import json
import datetime
import urllib2
from survey.views import *
from survey.ussd import USSD
from random import randint

class USSDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.ussd_params = {
                                'transactionId': "123344" + str(randint(1, 99999)),
                                'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
                                'msisdn': '256776520831',
                                'ussdServiceCode': '130',
                                'ussdRequestString': '',
                                'response': "false"
                            }
        self.investigator = Investigator.objects.create(name="investigator name", mobile_number=self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, ''))
        self.household = HouseHold.objects.create(name="HouseHold 1", investigator=self.investigator)
        survey = Survey.objects.create(name='Survey Name', description='Survey description')
        batch = Batch.objects.create(survey=survey)
        self.indicator = Indicator.objects.create(batch=batch)

    def test_numerical_questions(self):
        question_1 = Question.objects.create(indicator=self.indicator, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        question_2 = Question.objects.create(indicator=self.indicator, text="How many of them are male?", answer_type=Question.NUMBER, order=2)

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
        question_1 = Question.objects.create(indicator=self.indicator, text="How many members are there in this household?", answer_type=Question.TEXT, order=1)
        question_2 = Question.objects.create(indicator=self.indicator, text="How many of them are male?", answer_type=Question.TEXT, order=2)

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
        question_1 = Question.objects.create(indicator=self.indicator, text="How many members are there in this household?", answer_type=Question.MULTICHOICE, order=1)
        option_1_1 = QuestionOption.objects.create(question=question_1, text="OPTION 1", order=1)
        option_1_2 = QuestionOption.objects.create(question=question_1, text="OPTION 2", order=2)

        question_2 = Question.objects.create(indicator=self.indicator, text="How many of them are male?", answer_type=Question.MULTICHOICE, order=2)
        option_2_1 = QuestionOption.objects.create(question=question_2, text="OPTION 1", order=1)
        option_2_2 = QuestionOption.objects.create(question=question_2, text="OPTION 2", order=2)

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
        question = Question.objects.create(indicator=self.indicator, text="This is a question", answer_type=Question.MULTICHOICE)
        option_1 = QuestionOption.objects.create(question=question, text="OPTION 1", order=1)
        option_2 = QuestionOption.objects.create(question=question, text="OPTION 2", order=2)
        option_3 = QuestionOption.objects.create(question=question, text="OPTION 3", order=3)
        option_4 = QuestionOption.objects.create(question=question, text="OPTION 4", order=4)
        option_5 = QuestionOption.objects.create(question=question, text="OPTION 5", order=5)
        option_6 = QuestionOption.objects.create(question=question, text="OPTION 6", order=6)
        option_7 = QuestionOption.objects.create(question=question, text="OPTION 7", order=7)
        back_text = Question.PREVIOUS_PAGE_TEXT
        next_text = Question.NEXT_PAGE_TEXT

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
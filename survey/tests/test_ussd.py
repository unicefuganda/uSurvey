from django.test import TestCase
from django.test.client import Client
from survey.models import *
import json
import datetime
import urllib2
from survey.views import *

class USSDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.ussd_params = {
                                'transactionId': 123344,
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
        indicator = Indicator.objects.create(batch=batch)
        self.question_1 = Question.objects.create(indicator=indicator, text="How many members are there in this household?", answer_type=Question.NUMBER)
        self.question_2 = Question.objects.create(indicator=indicator, text="How many of them are male?", answer_type=Question.NUMBER)

    # def test_numerical_questions(self):
    #     response = self.client.post('/ussd', data=self.ussd_params)
    #     response_string = "responseString=%s&action=request" % self.question_1.text
    #     self.assertEquals(urllib2.unquote(response.content), response_string)
    #
    #     self.ussd_params['response'] = "true"
    #     self.ussd_params['ussdRequestString'] = "4"
    #
    #     response = self.client.post('/ussd', data=self.ussd_params)
    #     response_string = "responseString=%s&action=request" % self.question_2.text
    #     self.assertEquals(urllib2.unquote(response.content), response_string)
    #
    #     self.ussd_params['ussdRequestString'] = "2"
    #
    #     response = self.client.post('/ussd', data=self.ussd_params)
    #     response_string = "responseString=%s&action=end" % "Thanks for the survey."
    #     self.assertEquals(urllib2.unquote(response.content), response_string)
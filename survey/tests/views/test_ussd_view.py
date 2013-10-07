import datetime
import urllib2

from django.test import TestCase
from django.test.client import Client

from survey.ussd.ussd import USSD


class USSDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.ussd_params = {
            'transactionId': 123344,
            'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
            'msisdn': '256776520831',
            'ussdServiceCode': '130',
            'ussdRequestString': '',
            'response': 'false'
        }

    def test_ussd_url(self):
        response_message = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

        response = self.client.get('/ussd/', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

        client = Client(enforce_csrf_checks=True)
        response = self.client.post('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

        response = self.client.post('/ussd/', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

    def test_ussd_simulator(self):
        response = self.client.get('/ussd/simulator')
        self.failUnlessEqual(response.status_code, 200)
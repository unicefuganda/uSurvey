from random import randint
import datetime
from django.http import HttpRequest
from django.test.testcases import TestCase
from survey.models import NumericalAnswer


class USSDBaseTest(TestCase):
    def setUp(self):
        self.ussd_params = {
            'transactionId': "123344" + str(randint(1, 99999)),
            'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
            'msisdn': '2567765' + str(randint(1, 99999)),
            'ussdServiceCode': '130',
            'ussdRequestString': '',
            'response': "false"
        }

    def test_ussd_parameters_set_up(self):
        self.assertEqual('false', self.ussd_params['response'])
        self.assertEqual('', self.ussd_params['ussdRequestString'])
        self.assertEqual('130', self.ussd_params['ussdServiceCode'])

    def reset_session(self):
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))
        self.ussd_params['response'] = 'false'
        self.ussd_params['ussdRequestString'] = ''
        return self.client.post('/ussd', data=self.ussd_params)

    def select_samples(self):
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))
        self.ussd_params['response'] = 'false'
        self.ussd_params['ussdRequestString'] = ''
        self.client.post('/ussd', data=self.ussd_params)

        self.ussd_params['response'] = 'true'
        self.ussd_params['ussdRequestString'] = '100'
        return self.client.post('/ussd', data=self.ussd_params)

    def register_household(self):
        return self.respond('1')

    def take_survey(self):
        return self.respond("2")

    def select_household(self, household_id="1"):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = household_id
        return self.client.post('/ussd', data=self.ussd_params)

    def select_household_member(self, member_id="1"):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = member_id
        return self.client.post('/ussd', data=self.ussd_params)

    def respond(self, message):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = message
        return self.client.post('/ussd', data=self.ussd_params)

    def set_questions_answered_to_twenty_minutes_ago(self):
        for answer in NumericalAnswer.objects.all():
            answer.created -= datetime.timedelta(minutes=(20), seconds=1)
            answer.save()

    def hh_string(self, household_head):
        return "Household-%s-%s" % (household_head.household.random_sample_number, household_head.surname)


class FakeRequest(HttpRequest):
    def dict(self):
        obj = self.__dict__
        obj['transactionId'] = '1234567890'
        obj['response'] = 'false'
        return obj

    def __setitem__(self, key, value):
        obj = self.__dict__
        obj[key] = value
        return obj
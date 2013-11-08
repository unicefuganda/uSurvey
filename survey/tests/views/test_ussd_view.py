import datetime
import urllib2
from django.contrib.auth.models import User

from django.test.client import Client
from mock import patch
from rapidsms.contrib.locations.models import LocationType, Location
from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Investigator, Backend, RandomHouseHoldSelection, Household, Survey
from survey.tests.base_test import BaseTest

from survey.ussd.ussd import USSD


class USSDTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')

        self.client.login(username='Rajni', password='I_Rock')
        self.ussd_params = {
            'transactionId': 123344,
            'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
            'msisdn': '256776520831',
            'ussdServiceCode': '130',
            'ussdRequestString': '',
            'response': 'false'
        }
        self.backend = Backend.objects.create(name="Backend")
        self.location_type = LocationType.objects.create(name="District", slug="district")

    def test_url_without_open_survey_should_give_error_message(self):
        Investigator.objects.create(name='Inv1', location=Location.objects.create(name='Kampala', type=self.location_type),
                                        mobile_number=self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, ''),
                                        backend=self.backend)

        response_message = "responseString=%s&action=end" % USSD.MESSAGES['NO_OPEN_BATCH']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

    def test_ussd_url(self):
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        with patch.object(Survey, "currently_open_survey", return_value=open_survey):
            Investigator.objects.create(name='Inv1', location=Location.objects.create(name='Kampala', type=self.location_type),
                                        mobile_number=self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, ''),
                                        backend=self.backend)

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

    def test_should_know_to_respond_with_blocked_message_for_investigator_if_blocked(self):
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        with patch.object(Survey, "currently_open_survey", return_value=open_survey):
            investigator = Investigator.objects.create(name='Investigator 1', mobile_number='776520831', male=True, age=32,
                                                       backend=Backend.objects.create(name="Test"), is_blocked=True)
            Household.objects.create(investigator=investigator, location=investigator.location,
                                     uid=0, random_sample_number=1)

            response_message = "responseString=%s&action=end" % USSD.MESSAGES['INVESTIGATOR_BLOCKED_MESSAGE']
            response = self.client.get('/ussd', data=self.ussd_params)
            self.failUnlessEqual(response.status_code, 200)
            self.assertEquals(urllib2.unquote(response.content), response_message)

    def test_ussd_simulator(self):
        response = self.client.get('/ussd/simulator')
        self.failUnlessEqual(response.status_code, 200)

    def test_ussd_responds_with_household_count_if_investigator_is_registered_but_does_not_have_household_selection_sample(
            self):
        mobile_number = "123456789"
        investigator = Investigator.objects.create(mobile_number=mobile_number,
                                                   location=Location.objects.create(name="Kampala",
                                                                                    type=self.location_type),
                                                   backend=self.backend)
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        with patch.object(Survey, "currently_open_survey", return_value=open_survey):
            with patch.object(RandomHouseHoldSelection, 'generate') as generate_method:
                self.ussd_params['msisdn'] = investigator.mobile_number

                response = self.client.get('/ussd/', data=self.ussd_params)
                response_message = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']
                self.assertEquals(urllib2.unquote(response.content), response_message)

                self.ussd_params['ussdRequestString'] = '100'
                self.ussd_params['response'] = 'true'
                self.client.get('/ussd/', data=self.ussd_params)
                generate_method.assert_called_with(no_of_households=100, survey=open_survey)

    def test_sends_not_registered_message_if_investigator_is_not_registered(self):
        response = self.client.get('/ussd/', data=self.ussd_params)
        response_message = "responseString=%s&action=end" % USSD.MESSAGES['USER_NOT_REGISTERED']
        self.assertEquals(urllib2.unquote(response.content), response_message)

    def test_restricted_permission(self):
        self.assert_restricted_permission_for('/ussd/simulator/')
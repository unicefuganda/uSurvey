# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
import urllib2
from django.test import TestCase, Client
from rapidsms.backends.database.models import BackendMessage
from rapidsms.contrib.locations.models import Location, LocationType
from mock import patch
from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Backend, RandomHouseHoldSelection, Investigator, Survey
from survey.ussd.household_selection import HouseHoldSelection


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
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        with patch.object(Survey, "currently_open_survey", return_value=open_survey):
            mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)
            location_type = LocationType.objects.create(name="District", slug="district")

            Investigator.objects.create(name='Inv1', location=Location.objects.create(name='Kampala', type=location_type),
                                        mobile_number=mobile_number, backend=Backend.objects.create(name='Backend'))


            response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']
            response = self.client.get('/ussd', data=self.ussd_params)
            self.failUnlessEqual(response.status_code, 200)
            self.assertEquals(urllib2.unquote(response.content), response_message)
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

            self.ussd_params['response'] = "true"
            self.ussd_params['ussdRequestString'] = " 100 "

            response_message = "responseString=%s&action=end" % HouseHoldSelection.MESSAGES[
                'HOUSEHOLD_SELECTION_SMS_MESSAGE']
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

    def test_selection_for_survey_that_has_no_sampling(self):
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=False)
        with patch.object(Survey, "currently_open_survey", return_value=open_survey):
            mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)
            location_type = LocationType.objects.create(name="District", slug="district")

            Investigator.objects.create(name='Inv1', location=Location.objects.create(name='Kampala', type=location_type),
                                        mobile_number=mobile_number, backend=Backend.objects.create(name='Backend'))


            response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']

            response = self.client.get('/ussd', data=self.ussd_params)
            self.failUnlessEqual(response.status_code, 200)
            self.assertEquals(urllib2.unquote(response.content), response_message)
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

            self.ussd_params['response'] = "true"
            self.ussd_params['ussdRequestString'] = " 100 "

            response_message = "responseString=%s&action=end" % HouseHoldSelection.MESSAGES[
                'HOUSEHOLD_CONFIRMATION_MESSAGE']
            response = self.client.get('/ussd', data=self.ussd_params)
            self.failUnlessEqual(response.status_code, 200)
            self.assertEquals(urllib2.unquote(response.content), response_message)
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 1)

            household_selection = RandomHouseHoldSelection.objects.all()[0]
            self.assertEquals(household_selection.mobile_number, mobile_number)
            self.assertEquals(household_selection.no_of_households, 100)
            selected_households = household_selection.selected_households.split(',')
            self.assertEquals(len(selected_households), 100)

            message = BackendMessage.objects.filter(identity=self.ussd_params['msisdn'])
            self.failIf(message)

    def test_less_than_ten_households_failure(self):
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        with patch.object(Survey, "currently_open_survey", return_value=open_survey):
            mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)
            location_type = LocationType.objects.create(name="District", slug="district")

            Investigator.objects.create(name='Inv1', location=Location.objects.create(name='Kampala', type=location_type),
                                        mobile_number=self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, ''), backend=Backend.objects.create(name='Backend'))

            response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']
            response = self.client.get('/ussd', data=self.ussd_params)
            self.failUnlessEqual(response.status_code, 200)
            self.assertEquals(urllib2.unquote(response.content), response_message)

            self.ussd_params['response'] = "true"
            self.ussd_params['ussdRequestString'] = "9"

            response = self.client.get('/ussd', data=self.ussd_params)
            response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES[
                'HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE']
            self.assertEquals(urllib2.unquote(response.content), response_message)
            self.failUnlessEqual(response.status_code, 200)
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

            self.ussd_params['response'] = "true"
            self.ussd_params['ussdRequestString'] = "11"

            response_message = "responseString=%s&action=end" % HouseHoldSelection.MESSAGES[
                'HOUSEHOLD_SELECTION_SMS_MESSAGE']
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
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        with patch.object(Survey, "currently_open_survey", return_value=open_survey):
            mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)
            location_type = LocationType.objects.create(name="District", slug="district")

            Investigator.objects.create(name='Inv1', location=Location.objects.create(name='Kampala', type=location_type),
                                        mobile_number=self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, ''), backend=Backend.objects.create(name='Backend'))

            response_message = "responseString=%s&action=request" % HouseHoldSelection.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']
            response = self.client.get('/ussd', data=self.ussd_params)
            self.failUnlessEqual(response.status_code, 200)
            self.assertEquals(urllib2.unquote(response.content), response_message)
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

            self.ussd_params['response'] = "true"
            self.ussd_params['ussdRequestString'] = " 100 "

            response_message = "responseString=%s&action=end" % HouseHoldSelection.MESSAGES[
                'HOUSEHOLD_SELECTION_SMS_MESSAGE']
            response = self.client.get('/ussd', data=self.ussd_params)
            self.failUnlessEqual(response.status_code, 200)
            self.assertEquals(urllib2.unquote(response.content), response_message)
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 1)

            household_selection = RandomHouseHoldSelection.objects.all()[0]
            self.assertEquals(household_selection.mobile_number, mobile_number)
            self.assertEquals(household_selection.no_of_households, 100)
            selected_households = household_selection.selected_households.split(',')
            selected_households = map(int, selected_households)
            self.assertEquals(len(selected_households), 10)
            self.assertEqual(sorted(selected_households), selected_households)

            message = BackendMessage.objects.get(identity=self.ussd_params['msisdn'])
            self.assertEquals(message.text, household_selection.text_message())
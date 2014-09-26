# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
import urllib2
from django.test import TestCase, Client
from rapidsms.backends.database.models import BackendMessage
from rapidsms.contrib.locations.models import Location, LocationType
from mock import patch
from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Backend, RandomHouseHoldSelection, Investigator, Survey, EnumerationArea, Household
from survey.tests.ussd.ussd_base_test import USSDBaseTest
from survey.ussd.household_selection import HouseHoldSelection


class RandomHouseHoldSelectionTest(USSDBaseTest):
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

        self.open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        self.location_type = LocationType.objects.create(name="District", slug="district")
        self.masaka = Location.objects.create(name="Masaka", type=self.location_type)
        self.ea = EnumerationArea.objects.create(name="EA2", survey=self.open_survey)
        self.ea.locations.add(self.masaka)
        mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '', 1)
        self.investigator = Investigator.objects.create(name='Inv1', ea=self.ea, mobile_number=mobile_number,
                                    backend=Backend.objects.create(name='Backend'))


    def test_selection(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

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
            mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '', 1)
            self.assertEquals(household_selection.mobile_number, mobile_number)
            self.assertEquals(household_selection.no_of_households, 100)
            selected_households = household_selection.selected_households.split(',')
            self.assertEquals(len(selected_households), 10)

            message = BackendMessage.objects.get(identity=self.ussd_params['msisdn'])
            self.assertEquals(message.text, household_selection.text_message())

    def test_HH_selection_creates_HH(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            self.assertEquals(Household.objects.count(), 0)
            self.client.post('/ussd', data=self.ussd_params)
            response = self.respond(" 100 ")
            households = Household.objects.all()
            self.assertEqual(self.open_survey.sample_size, households.count())
            self.assertEqual(self.open_survey.sample_size, households.filter(ea=self.ea, investigator=self.investigator).count())



    def test_selection_for_survey_that_has_no_sampling(self):
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=False)
        with patch.object(Survey, "currently_open_survey", return_value=open_survey):
            mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '', 1)
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

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
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

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
            mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '', 1)
            self.assertEquals(household_selection.mobile_number, mobile_number)
            self.assertEquals(household_selection.no_of_households, 11)
            selected_households = household_selection.selected_households.split(',')
            self.assertEquals(len(selected_households), 10)

            message = BackendMessage.objects.get(identity=self.ussd_params['msisdn'])
            self.assertEquals(message.text, household_selection.text_message())

    def test_sort_household_selection_list(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mobile_number = self.ussd_params['msisdn'].replace(COUNTRY_PHONE_CODE, '', 1)
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)

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
    def test_transition_random_HH_selection_to_register_HHmember(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            self.assertEquals(RandomHouseHoldSelection.objects.count(), 0)
            self.client.get('/ussd', data=self.ussd_params)
            self.respond(" 100 ")

            some_age = 10
            answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
                }

            self.generate_register_HH_questions()

            self.reset_session()
            self.choose_menu_to_register_household()
            selected_household_id = '2'
            self.select_household(selected_household_id)
            self.respond('2')
            self.respond(answers['name'])
            self.respond(answers['age'])
            self.respond(answers['month'])
            self.respond(answers['year'])
            self.respond(answers['gender'])

            selected_household = Household.objects.get(uid=selected_household_id)
            self.assertEqual(1, selected_household.household_member.count())
            member = selected_household.household_member.all()[0]
            self.assertEqual(member.surname, answers['name'])
            self.assertEqual(member.male, True)
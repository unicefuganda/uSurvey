from random import randint
import datetime
import urllib2

from mock import patch
from django.test import Client
from rapidsms.contrib.locations.models import Location

from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Backend, Survey, Investigator, Household, Batch, RandomHouseHoldSelection
from survey.tests.ussd.ussd_base_test import USSDBaseTest
from survey.ussd.ussd import USSD
from survey.ussd.ussd_survey import USSDSurvey


class USSDRegisteringHouseholdTest(USSDBaseTest):
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
        self.backend = Backend.objects.create(name='something')
        self.open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        self.batch = Batch.objects.create(order=1, name="Batch A", survey=self.open_survey)
        self.kampala = Location.objects.create(name="Kampala")
        self.entebbe = Location.objects.create(name="Entebbe")

        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number=self.ussd_params['msisdn'].replace(
                                                            COUNTRY_PHONE_CODE, ''),
                                                        location=self.kampala,
                                                        backend=self.backend)

        self.household1 = self.create_household(1)
        self.household2 = self.create_household(2)
        self.household3 = self.create_household(3)
        self.household4 = self.create_household(4)

    def create_household(self, unique_id):
        return Household.objects.create(investigator=self.investigator, location=self.investigator.location,
                                        uid=unique_id, random_sample_number=unique_id, survey=self.open_survey)

    def test_shows_non_response_menu_if_its_activated(self):
        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()
                    homepage = "Welcome %s to the survey.\n1:" \
                               " Register households\n2: " \
                               "Take survey\n3: " \
                               "Report non-response" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEqual(urllib2.unquote(response.content), response_string)

    def test_does_not_show_non_response_menu_if_its_not_deactivated(self):
        self.batch.deactivate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()
                    homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEqual(urllib2.unquote(response.content), response_string)

    def test_shows_only_households_that_have_not_completed(self):
        self.household1.batch_completed(self.batch)
        self.household2.batch_completed(self.batch)
        self.household3.batch_completed(self.batch)

        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                    response = self.report_non_response()
                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: Household-%s" % self.household4.uid
                    first_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)

    def test_paginates_non_completed_households_list(self):
        household5 = self.create_household(5)
        household6 = self.create_household(6)
        household7 = self.create_household(7)
        household8 = self.create_household(8)
        household9 = self.create_household(9)
        household10 = self.create_household(10)

        self.household1.batch_completed(self.batch)

        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                    response = self.report_non_response()
                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: Household-%s" \
                                                                       "\n2: Household-%s" \
                                                                       "\n3: Household-%s" \
                                                                       "\n4: Household-%s" \
                                                                       "\n#: Next" % (
                                         self.household2.uid, self.household3.uid, self.household4.uid, household5.uid)
                    first_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)
                    response = self.respond("#")

                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n5: Household-%s" \
                                                                       "\n6: Household-%s" \
                                                                       "\n7: Household-%s" \
                                                                       "\n8: Household-%s" \
                                                                       "\n*: Back\n#: Next" % (
                                         household6.uid, household7.uid, household8.uid, household9.uid)
                    second_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), second_page_list)

                    response = self.respond("#")

                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n9: Household-%s" \
                                                                       "\n*: Back" % household10.uid
                    last_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), last_page_list)

                    response = self.respond("*")
                    self.assertEquals(urllib2.unquote(response.content), second_page_list)

                    response = self.respond("*")
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)

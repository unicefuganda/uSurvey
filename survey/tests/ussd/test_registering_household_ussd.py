from random import randint
import datetime
import urllib2
from django.test import Client
from rapidsms.contrib.locations.models import Location
from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Investigator, Backend, Household
from survey.tests.ussd.ussd_base_test import USSDBaseTest
from survey.ussd.ussd import USSD


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
        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number=self.ussd_params['msisdn'].replace(
                                                            COUNTRY_PHONE_CODE, ''),
                                                        location=Location.objects.create(name="Kampala"),
                                                        backend=Backend.objects.create(name='something'))

        self.household1 = self.create_household(0)
        self.household2 = self.create_household(1)
        self.household3 = self.create_household(2)
        self.household4 = self.create_household(3)
        self.household5 = self.create_household(4)

    def create_household(self, unique_id):
        return Household.objects.create(investigator=self.investigator, location=self.investigator.location, uid=unique_id)

    def test_should_show_list_of_households_with_UIds_when_selected_option_to_register_household_and_pagination(self):
        self.reset_session()
        response = self.register_household()
        household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: Household-%s\n2: Household-%s\n3: Household-%s\n4: Household-%s\n#: Next" % (
            self.household1.uid, self.household2.uid, self.household3.uid, self.household4.uid)

        first_page_HH_list = "responseString=%s&action=request" % (household_list)
        self.assertEquals(urllib2.unquote(response.content), first_page_HH_list)

        response = self.respond("#")

        household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n5: Household-%s\n*: Back" % (self.household5.uid)

        response_string = "responseString=%s&action=request" % (household_list)
        self.assertEquals(urllib2.unquote(response.content), response_string)

        response = self.respond("*")
        self.assertEquals(urllib2.unquote(response.content), first_page_HH_list)

    def test_should_ask_for_head_or_member_after_selecting_household(self):
        self.reset_session()
        self.register_household()

        response = self.select_household("2")

        ask_member_response_string = "responseString=%s&action=request" % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER']
        self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    





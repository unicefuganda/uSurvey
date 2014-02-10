import datetime
import urllib2

from random import randint

from django.test.client import Client
from mock import patch
from rapidsms.contrib.locations.models import LocationType, Location
from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import HouseholdMemberGroup, GroupCondition, BatchQuestionOrder, Survey, RandomHouseHoldSelection, EnumerationArea
from survey.models.backend import Backend
from survey.models.household_batch_completion import HouseholdMemberBatchCompletion
from survey.models.batch import Batch
from survey.models.households import HouseholdHead, Household
from survey.models.investigator import Investigator

from survey.models.question import Question
from survey.tests.ussd.ussd_base_test import USSDBaseTest
from survey.ussd.ussd import *
from survey.ussd.ussd_survey import USSDSurvey


class USSDOpenBatchTest(USSDBaseTest):
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
        self.open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        city = LocationType.objects.create(name="City")
        self.mbarara = Location.objects.create(name="Mbarara", type=city)
        self.ea = EnumerationArea.objects.create(name="EA2", survey=self.open_survey)
        self.ea.locations.add(self.mbarara)

        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number=self.ussd_params['msisdn'].replace(
                                                            COUNTRY_PHONE_CODE, ''),
                                                        ea=self.ea,
                                                        backend=Backend.objects.create(name='something'))
        self.household = Household.objects.create(investigator=self.investigator, ea=self.investigator.ea,
                                                  survey=self.open_survey, uid=0)
        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname",
                                                           date_of_birth='1980-09-01')
        self.household_head_1 = HouseholdHead.objects.create(
            household=Household.objects.create(investigator=self.investigator, survey=self.open_survey,
                                               location=self.investigator.location, uid=1),
            surname="Name " + str(randint(1, 9999)), date_of_birth='1980-09-01')
        Batch.objects.create(order=1, survey=self.open_survey)

    def test_closed_batch(self):
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                response = self.choose_menu_to_take_survey()
                response_string = "responseString=%s&action=end" % USSD.MESSAGES['NO_OPEN_BATCH']
                self.assertEquals(urllib2.unquote(response.content), response_string)


class USSDWithMultipleBatches(USSDBaseTest):
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
        self.open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        self.ea = EnumerationArea.objects.create(name="EA2", survey=self.open_survey)
        self.ea.locations.add(self.location)

        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number=self.ussd_params['msisdn'].replace(
                                                            COUNTRY_PHONE_CODE, ''), ea=self.ea,
                                                        backend=Backend.objects.create(name='something'))

        self.household = Household.objects.create(investigator=self.investigator, ea=self.investigator.ea,
                                                  survey=self.open_survey, uid=0)
        self.female_group = HouseholdMemberGroup.objects.create(name="Female", order=1)
        self.condition = GroupCondition.objects.create(value=False, attribute="GENDER", condition="EQUALS")

        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname",
                                                           date_of_birth='1929-02-02', male=False)
        self.household_head_1 = HouseholdHead.objects.create(
            household=Household.objects.create(investigator=self.investigator, location=self.investigator.location, uid=1),
            surname="Name " + str(randint(1, 9999)), date_of_birth='1929-02-02', male=False)
        self.batch = Batch.objects.create(order=1, survey=self.open_survey)
        self.question_1 = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER,
                                                  order=1, group=self.female_group)
        self.question_2 = Question.objects.create(text="Question 2?", answer_type=Question.NUMBER,
                                                  order=2, group=self.female_group)

        self.question_1.batches.add(self.batch)
        self.question_2.batches.add(self.batch)

        BatchQuestionOrder.objects.create(batch=self.batch, question=self.question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=self.question_2, order=2)

        self.batch_1 = Batch.objects.create(order=2, survey=self.open_survey)
        self.question_3 = Question.objects.create(text="Question 3?", answer_type=Question.NUMBER,
                                                  order=3, group=self.female_group)
        self.question_4 = Question.objects.create(text="Question 4?", answer_type=Question.NUMBER,
                                                  order=4, group=self.female_group)
        self.question_3.batches.add(self.batch_1)
        self.question_4.batches.add(self.batch_1)
        BatchQuestionOrder.objects.create(batch=self.batch_1, question=self.question_3, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch_1, question=self.question_4, order=2)

    def test_with_one_batch_open(self):
        self.batch.open_for_location(self.location)

        self.assertEquals(HouseholdMemberBatchCompletion.objects.count(), 0)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(USSDSurvey, 'is_active', return_value=False):
                self.reset_session()

                self.choose_menu_to_take_survey()
                self.select_household()
                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % self.question_1.to_ussd()
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("1")
                response_string = "responseString=%s&action=request" % self.question_2.to_ussd()
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("1")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(HouseholdMemberBatchCompletion.objects.count(), 1)
                household_completed = HouseholdMemberBatchCompletion.objects.latest('id')
                self.assertEquals(household_completed.household, self.household)
                self.assertEquals(household_completed.investigator, self.investigator)
                self.assertEquals(household_completed.batch, self.batch)

    def test_with_two_batch_open(self):
        self.batch.open_for_location(self.location)
        self.batch_1.open_for_location(self.location)

        self.assertEquals(HouseholdMemberBatchCompletion.objects.count(), 0)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(USSDSurvey, 'is_active', return_value=False):
                self.reset_session()

            self.choose_menu_to_take_survey()
            self.select_household()
            response = self.select_household_member()
            response_string = "responseString=%s&action=request" % self.question_1.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.respond("1")
            response_string = "responseString=%s&action=request" % self.question_2.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.respond("1")
            response_string = "responseString=%s&action=request" % self.question_3.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            self.assertEquals(HouseholdMemberBatchCompletion.objects.count(), 1)
            household_completed = HouseholdMemberBatchCompletion.objects.latest('id')
            self.assertEquals(household_completed.household, self.household)
            self.assertEquals(household_completed.householdmember, self.household_head.get_member())
            self.assertEquals(household_completed.investigator, self.investigator)
            self.assertEquals(household_completed.batch, self.batch)

            response = self.respond("1")
            response_string = "responseString=%s&action=request" % self.question_4.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.respond("1")
            response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
            self.assertEquals(urllib2.unquote(response.content), response_string)

            self.assertEquals(HouseholdMemberBatchCompletion.objects.count(), 2)
            household_completed = HouseholdMemberBatchCompletion.objects.latest('id')
            self.assertEquals(household_completed.household, self.household)
            self.assertEquals(household_completed.householdmember, self.household_head.get_member())
            self.assertEquals(household_completed.investigator, self.investigator)
            self.assertEquals(household_completed.batch, self.batch_1)

    def test_with_second_batch_open(self):
        self.batch_1.open_for_location(self.location)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(USSDSurvey, 'is_active', return_value=False):
                self.reset_session()

            self.choose_menu_to_take_survey()
            self.select_household()
            response = self.select_household_member()

            response_string = "responseString=%s&action=request" % self.question_3.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.respond("1")
            response_string = "responseString=%s&action=request" % self.question_4.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.respond("1")
            response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
            self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_with_batch_open_for_parent_location(self):
        self.batch.open_for_location(self.uganda)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(USSDSurvey, 'is_active', return_value=False):
                self.reset_session()

            self.choose_menu_to_take_survey()
            self.select_household()
            response = self.select_household_member()
            response_string = "responseString=%s&action=request" % self.question_1.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.respond("1")
            response_string = "responseString=%s&action=request" % self.question_2.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.respond("1")
            response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
            self.assertEquals(urllib2.unquote(response.content), response_string)



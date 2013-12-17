# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
from random import randint
import urllib2
from django.test import TestCase, Client
from mock import patch
from rapidsms.contrib.locations.models import LocationType, Location
from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Investigator, Backend, Household, HouseholdHead, Batch, HouseholdMemberGroup, GroupCondition, Question, BatchQuestionOrder, Survey, RandomHouseHoldSelection, EnumerationArea
from survey.models.households import HouseholdMember
from survey.tests.ussd.ussd_base_test import USSDBaseTest
from survey.ussd.ussd_survey import USSDSurvey


class USSDHouseholdMemberQuestionNavigationTest(USSDBaseTest):
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
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.district = LocationType.objects.create(name='District', slug='district')
        self.location = Location.objects.create(name="Kampala", type=self.district, tree_parent=self.uganda)
        ea = EnumerationArea.objects.create(name="EA2", survey=self.open_survey)
        ea.locations.add(self.location)

        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number=self.ussd_params['msisdn'].replace(
                                                            COUNTRY_PHONE_CODE, ''), ea=ea,
                                                        backend=Backend.objects.create(name='something'))
        self.household = Household.objects.create(investigator=self.investigator, ea=self.investigator.ea,
                                                  survey=self.open_survey, uid=0)
        self.household_head = HouseholdHead.objects.create(household=self.household, male=False, surname="Surname",
                                                           date_of_birth=datetime.date(1929, 2, 2))
        self.household_member = HouseholdMember.objects.create(surname="Surnmae", household=self.household,
                                                               date_of_birth=datetime.date(1929, 2, 2), male=False)

        self.batch = Batch.objects.create(order=1, survey=self.open_survey)

        self.general_group = HouseholdMemberGroup.objects.create(name="General Group", order=0)
        self.female_group = HouseholdMemberGroup.objects.create(name="Female", order=1)
        self.condition = GroupCondition.objects.create(value=False, attribute="GENDER", condition="EQUALS")
        self.general_condition = GroupCondition.objects.create(value=True, attribute="GENERAL", condition="EQUALS")

        self.condition.groups.add(self.female_group)
        self.general_condition.groups.add(self.general_group)

        self.question_1 = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER,
                                                  order=1, group=self.general_group)
        self.question_2 = Question.objects.create(text="Question 2?", answer_type=Question.NUMBER,
                                                  order=2, group=self.general_group)

        self.question_3 = Question.objects.create(text="Question 3?", answer_type=Question.NUMBER,
                                                  order=3, group=self.general_group)
        self.question_4 = Question.objects.create(text="Question 4?", answer_type=Question.NUMBER,
                                                  order=4, group=self.general_group)

        self.question_5 = Question.objects.create(text="Question 5?", answer_type=Question.NUMBER,
                                                  order=1, group=self.female_group)

        self.question_6 = Question.objects.create(text="Question 6?", answer_type=Question.NUMBER,
                                                  order=2, group=self.female_group)
        order = 1
        for question in [self.question_1, self.question_2, self.question_3, self.question_4, self.question_5, self.question_6 ]:
            BatchQuestionOrder.objects.create(batch=self.batch, question=question, order=order)
            question.batches.add(self.batch)
            order += 1

    def select_household(self, household=1):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = "00"
        self.client.post('/ussd', data=self.ussd_params)
        self.ussd_params['ussdRequestString'] = str(household)
        return self.client.post('/ussd', data=self.ussd_params)

    def select_household_member(self, member_id="1"):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = member_id
        return self.client.post('/ussd', data=self.ussd_params)

    def test_knows_to_select_the_first_general_question_for_household_head(self):
        self.batch.open_for_location(self.location)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(USSDSurvey, 'is_active', return_value=False):
                self.reset_session()

            self.take_survey()
            self.select_household()

            response = self.select_household_member()
            response_string = "responseString=%s&action=request" % self.question_1.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

    def answer_ussd_question(self, answer):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = str(answer)
        response = self.client.post('/ussd', data=self.ussd_params)
        return response

    def test_knows_to_not_select_the_general_questions_for_household_member(self):
        self.batch.open_for_location(self.location)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(USSDSurvey, 'is_active', return_value=False):
                response = self.reset_session()
            self.take_survey()
            self.batch.open_for_location(self.location)
            self.select_household()

            response = self.select_household_member("2")
            response_string = "responseString=%s&action=request" % self.question_5.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.answer_ussd_question("1")
            response_string = "responseString=%s&action=request" % self.question_6.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_head_knows_how_to_get_questions_in_other_groups_when_general_questions_are_done(self):
        self.batch.open_for_location(self.location)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(USSDSurvey, 'is_active', return_value=False):
                self.reset_session()

            self.take_survey()
            self.select_household()

            response = self.select_household_member()
            response_string = "responseString=%s&action=request" % self.question_1.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.answer_ussd_question("1")

            response_string = "responseString=%s&action=request" % self.question_2.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.answer_ussd_question("1")

            response_string = "responseString=%s&action=request" % self.question_3.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.answer_ussd_question("1")

            response_string = "responseString=%s&action=request" % self.question_4.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.answer_ussd_question("1")

            response_string = "responseString=%s&action=request" % self.question_5.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.answer_ussd_question("1")

            response_string = "responseString=%s&action=request" % self.question_6.to_ussd()
            self.assertEquals(urllib2.unquote(response.content), response_string)
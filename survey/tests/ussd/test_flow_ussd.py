# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
from random import randint
import urllib2
from django.test import TestCase, Client
from mock import patch
from rapidsms.contrib.locations.models import Location
from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Household, HouseholdHead, Investigator, Backend, HouseholdMemberGroup, GroupCondition, Batch, Question, NumericalAnswer, HouseholdMemberBatchCompletion, QuestionModule, BatchQuestionOrder, Survey, RandomHouseHoldSelection
from survey.models.households import HouseholdMember
from survey.tests.ussd.ussd_base_test import USSDBaseTest
from survey.ussd.ussd import USSD
from survey.ussd.ussd_survey import USSDSurvey


class USSDTestCompleteFlow(USSDBaseTest):
    def create_household_head(self, uid):
        self.household = Household.objects.create(investigator=self.investigator, location=self.investigator.location,
                                                  uid=uid, survey=self.open_survey_1)
        return HouseholdHead.objects.create(household=self.household,
                                            surname="Name " + str(randint(1, 9999)),
                                            date_of_birth=datetime.date(1980, 9, 1))

    def post_ussd_response(self, response="true", request_string="1"):
        self.ussd_params['response'] = response
        self.ussd_params['ussdRequestString'] = request_string
        return self.client.post('/ussd', data=self.ussd_params)

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
        self.kampala = Location.objects.create(name="Kampala")
        self.backend = Backend.objects.create(name='test')
        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number=self.ussd_params['msisdn'].replace(
                                                            COUNTRY_PHONE_CODE, ''),
                                                        location=self.kampala,
                                                        backend=self.backend)

        self.head_group = HouseholdMemberGroup.objects.create(name="General", order=1)
        self.condition = GroupCondition.objects.create(value='HEAD', attribute="GENERAL", condition="EQUALS")
        self.condition.groups.add(self.head_group)

        self.member_group = HouseholdMemberGroup.objects.create(name="Less than 10", order=2)
        self.member_condition = GroupCondition.objects.create(value=10, attribute="AGE", condition="LESS_THAN")
        self.member_condition.groups.add(self.member_group)

        self.open_survey_1 = Survey.objects.create(name="open survey one", description="open survey", has_sampling=True)

        self.household_head_1 = self.create_household_head(0)
        self.household_head_2 = self.create_household_head(1)
        self.household_head_3 = self.create_household_head(2)
        self.household_head_4 = self.create_household_head(3)
        self.household_head_5 = self.create_household_head(4)
        self.household_head_6 = self.create_household_head(5)
        self.household_head_7 = self.create_household_head(6)
        self.household_head_8 = self.create_household_head(7)
        self.household_head_9 = self.create_household_head(8)


        self.batch = Batch.objects.create(name="Batch A", order=1, survey=self.open_survey_1)
        self.batch_b = Batch.objects.create(name="Batch B", order=2, survey=self.open_survey_1)
        self.batch.open_for_location(self.investigator.location)
        self.question_1 = Question.objects.create(text="Question 1",
                                                  answer_type=Question.NUMBER, order=0, group=self.head_group)

        self.question_2 = Question.objects.create(text="Question 2",
                                                  answer_type=Question.NUMBER, order=1, group=self.head_group)
        self.question_1_b = Question.objects.create(text="Question 1b ",
                                                    answer_type=Question.NUMBER, order=2, group=self.head_group)
        self.question_3 = Question.objects.create(text="Question 3",
                                                  answer_type=Question.NUMBER, order=0, group=self.member_group)

        self.question_1.batches.add(self.batch)
        self.question_2.batches.add(self.batch)
        self.question_3.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=self.question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=self.question_2, order=2)
        BatchQuestionOrder.objects.create(batch=self.batch, question=self.question_3, order=3)

        self.question_1_b.batches.add(self.batch_b)
        BatchQuestionOrder.objects.create(batch=self.batch_b, question=self.question_1_b, order=1)

    def create_household_member(self, member_name, household):
        return HouseholdMember.objects.create(surname="member %s" % member_name,
                                              date_of_birth=datetime.date(2012, 2, 2), male=True,
                                              household=household)

    def test_household_member_list_paginates(self):
        household = Household.objects.get(uid=0, survey=self.open_survey_1)
        member_1 = self.create_household_member("1", household)
        member_2 = self.create_household_member("2", household)
        member_3 = self.create_household_member("3", household)
        member_4 = self.create_household_member("4", household)
        member_5 = self.create_household_member("5", household)
        member_6 = self.create_household_member("6", household)
        member_7 = self.create_household_member("7", household)

        member_list_1 = "%s\n1: %s - (HEAD)\n2: %s\n3: %s\n4: %s\n#: Next" % (
            USSD.MESSAGES['MEMBERS_LIST'], self.household_head_1.surname, member_1.surname,
            member_2.surname, member_3.surname)

        member_list_2 = "%s\n5: %s\n6: %s\n7: %s\n8: %s\n*: Back" % (
            USSD.MESSAGES['MEMBERS_LIST'], member_4.surname, member_5.surname,
            member_6.surname, member_7.surname)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                response = self.select_household()
                response_string = "responseString=%s&action=request" % member_list_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "#"
                response = self.client.post('/ussd', data=self.ussd_params)

                response_string = "responseString=%s&action=request" % member_list_2
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "*"
                response = self.client.post('/ussd', data=self.ussd_params)

                response_string = "responseString=%s&action=request" % member_list_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "100"
                response = self.client.post('/ussd', data=self.ussd_params)

                response_string = "responseString=%s&action=request" % ("INVALID SELECTION: " + member_list_1)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "asda"
                response = self.client.post('/ussd', data=self.ussd_params)

                response_string = "responseString=%s&action=request" % ("INVALID SELECTION: " + member_list_1)
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def set_questions_answered_to_twenty_minutes_ago(self):
        for answer in NumericalAnswer.objects.all():
            answer.created -= datetime.timedelta(minutes=(20), seconds=1)
            answer.save()

    def test_flow(self):
        self.batch.open_for_location(self.investigator.location)
        self.batch_b.close_for_location(self.investigator.location)
        household1_member = self.create_household_member("Member 1", self.household_head_1.household)
        household2_member = self.create_household_member("Member 2", self.household_head_2.household)

        homepage = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                households_list_1 = "%s\n1: %s\n2: %s\n3: %s\n4: %s\n#: Next" % (
                    USSD.MESSAGES['HOUSEHOLD_LIST'], self.hh_string(self.household_head_1), self.hh_string(self.household_head_2),
                    self.hh_string(self.household_head_3), self.hh_string(self.household_head_4))

                households_list_2 = "%s\n5: %s\n6: %s\n7: %s\n8: %s\n*: Back\n#: Next" % (
                    USSD.MESSAGES['HOUSEHOLD_LIST'], self.hh_string(self.household_head_5), self.hh_string(self.household_head_6),
                    self.hh_string(self.household_head_7), self.hh_string(self.household_head_8))

                households_list_3 = "%s\n9: %s\n*: Back" % (USSD.MESSAGES['HOUSEHOLD_LIST'], self.hh_string(self.household_head_9))

                response = self.take_survey()
                response_string = "responseString=%s&action=request" % households_list_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "#"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % households_list_2
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "#"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % households_list_3
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "*"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % households_list_2
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "*"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % households_list_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "100"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % ("INVALID SELECTION: " + households_list_1)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "adss"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % ("INVALID SELECTION: " + households_list_1)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "1"

                self.client.post('/ussd', data=self.ussd_params)

                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "10"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % self.question_2.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(10, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_1,
                                                                  householdmember=self.household_head_1).answer)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "5"
                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(5, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_2,
                                                                 household=self.household_head_1.household).answer)

                # Deleting all the households except 1 and 2

                self.household_head_3.household.delete()
                self.household_head_4.household.delete()
                self.household_head_5.household.delete()
                self.household_head_6.household.delete()
                self.household_head_7.household.delete()
                self.household_head_8.household.delete()
                self.household_head_9.household.delete()

                # Survey for the next household

                self.set_questions_answered_to_twenty_minutes_ago()

                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()

                response_string = "responseString=%s&action=request" % homepage
                self.assertEquals(urllib2.unquote(response.content), response_string)

                households_list_1 = "%s\n1: %s\n2: %s" % (
                    USSD.MESSAGES['HOUSEHOLD_LIST'], self.hh_string(self.household_head_1), self.hh_string(self.household_head_2))

                response = self.take_survey()
                response_string = "responseString=%s&action=request" % households_list_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "2"

                self.client.post('/ussd', data=self.ussd_params)
                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "10"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % self.question_2.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(10, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_1,
                                                                  household=self.household_head_2.household).answer)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "5"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "1"

                response = self.client.post('/ussd', data=self.ussd_params)
                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "2"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % self.question_3.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "20"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "2"

                response = self.client.post('/ussd', data=self.ussd_params)
                households_list = "%s\n1: %s\n2: %s*" % (
                    USSD.MESSAGES['HOUSEHOLD_LIST'], self.hh_string(self.household_head_1), self.hh_string(self.household_head_2))
                response_string = "responseString=%s&action=request" % households_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "1"

                response = self.client.post('/ussd', data=self.ussd_params)

                households_member_list = "%s\n1: %s - (HEAD)*\n2: %s" % (
                    USSD.MESSAGES['MEMBERS_LIST'], self.household_head_1.surname, household1_member.surname)
                response_string = "responseString=%s&action=request" % households_member_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("2")

                response_string = "responseString=%s&action=request" % self.question_3.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = "30"

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)


                self.ussd_params['response'] = "true"
                self.ussd_params['ussdRequestString'] = USSD.ANSWER['NO']

                response = self.client.post('/ussd', data=self.ussd_params)
                response_string = "responseString=%s&action=end" % USSD.MESSAGES['SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(5, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_2,
                                                                 household=self.household_head_2.household).answer)
                self.assertEquals(20, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_3,
                                                                  household=self.household_head_2.household).answer)
                self.assertEquals(30, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_3,
                                                                  household=self.household_head_1.household).answer)

    def test_should_ask_to_resume_questions_or_go_back_to_member_list_upon_session_timeout_or_session_cancel(self):
        question_4 = Question.objects.create(text="Question 4",
                                                  answer_type=Question.NUMBER, order=3, group=self.head_group)
        question_4.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_4, order=3)

        homepage = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()
                response_string = "responseString=%s&action=request" % homepage
                self.assertEquals(urllib2.unquote(response.content), response_string)
                self.take_survey()
                self.select_household()
                self.select_household_member()
                self.respond("1")

                response = self.reset_session()

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['YES'])
                response_string = "responseString=%s&action=request" % self.question_2.text
                batch= Batch.open_ordered_batches(self.household_head_1.get_location())[0]
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond('1')
                response_string = "responseString=%s&action=request" % question_4.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.reset_session()
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['NO'])
                households_member_list = "%s\n1: %s - (HEAD)" % (USSD.MESSAGES['MEMBERS_LIST'], self.household_head_1.surname)
                response_string = "responseString=%s&action=request" % households_member_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_renders_no_households_message_if_investigator_is_in_open_survey_location_but_has_no_households(self):
        entebbe = Location.objects.create(name="Entebbe")
        another_open_survey = Survey.objects.create(name="another open survey", description="open survey", has_sampling=True)

        investigator = Investigator.objects.create(name="new investigator",
                                                        mobile_number='123406489',
                                                        location=entebbe,
                                                        backend=self.backend)

        Household.objects.create(investigator=investigator, location=investigator.location,
                                                  uid=16, survey=self.open_survey_1)

        location_batch = Batch.objects.create(name="Batch B", order=6, survey=another_open_survey)
        location_batch.open_for_location(entebbe)
        homepage = USSD.MESSAGES['WELCOME_TEXT'] % investigator.name

        with patch.object(Investigator.objects, "get", return_value=investigator):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEquals(urllib2.unquote(response.content), response_string)
                    response = self.take_survey()

                    response_string = "responseString=%s&action=end" % USSD.MESSAGES['NO_HOUSEHOLDS']
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_should_show_household_list_if_resuming_survey_and_last_answered_question_was_more_than_timeout(self):
        question_4 = Question.objects.create(text="Question 4",
                                                  answer_type=Question.NUMBER, order=3, group=self.head_group)
        question_4.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_4, order=3)

        homepage = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()
                response_string = "responseString=%s&action=request" % homepage
                self.assertEquals(urllib2.unquote(response.content), response_string)
                self.take_survey()
                self.select_household()
                self.select_household_member()
                self.respond("1")

                response = self.reset_session()

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                with patch.object(Investigator, "was_active_within", return_value=False):
                    response = self.respond(USSD.ANSWER['YES'])
                    households_list_1 = "%s\n1: %s\n2: %s\n3: %s\n4: %s\n#: Next" % (USSD.MESSAGES['HOUSEHOLD_LIST'],
                                                                                 self.hh_string(self.household_head_1),
                                                                                 self.hh_string(self.household_head_2),
                                                                                 self.hh_string(self.household_head_3),
                                                                                 self.hh_string(self.household_head_4),)
                    response_string = "responseString=%s&action=request" % households_list_1
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                    self.respond('2')
                    self.reset_session()
                    response = self.respond(USSD.ANSWER['YES'])
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                    self.reset_session()
                    response = self.respond(USSD.ANSWER['NO'])
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                    self.reset_session()
                    response = self.respond(USSD.ANSWER['YES'])
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                    self.respond('1')
                    batch= Batch.open_ordered_batches(self.household_head_1.get_location())[0]

                    response = self.respond('1')
                    response_string = "responseString=%s&action=request" % self.question_2.text
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                    response = self.respond('1')
                    response_string = "responseString=%s&action=request" % question_4.text
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_show_completion_star_next_to_household_head_name(self):
        self.household_head_1.batch_completed(self.batch)
        self.household_head_3.batch_completed(self.batch)
        homepage = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()

                response_string = "responseString=%s&action=request" % homepage
                self.assertEquals(urllib2.unquote(response.content), response_string)

                households_list_1 = "%s\n1: %s*\n2: %s\n3: %s*\n4: %s\n#: Next" % (
                    USSD.MESSAGES['HOUSEHOLD_LIST'], self.hh_string(self.household_head_1), self.hh_string(self.household_head_2),
                    self.hh_string(self.household_head_3), self.hh_string(self.household_head_4))

                response = self.take_survey()
                response_string = "responseString=%s&action=request" % households_list_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_completed_batch_timeout_for_household_after_5_min_should_allow_other_batches(self):
        self.household_head_1.household.batch_completed(self.batch)
        self.investigator.member_answered(self.question_1, self.household_head_1, 1, self.batch)
        self.investigator.member_answered(self.question_2, self.household_head_1, 1, self.batch)

        latest_answer = NumericalAnswer.objects.all().latest()
        latest_answer.created -= datetime.timedelta(minutes=(USSD.TIMEOUT_MINUTES + 1), seconds=1)
        latest_answer.save()

        answer_one = NumericalAnswer.objects.filter(question=self.question_1)[0]
        answer_one.created -= datetime.timedelta(minutes=(USSD.TIMEOUT_MINUTES + 2), seconds=1)
        answer_one.save()

        self.batch.close_for_location(self.investigator.location)
        self.batch_b.open_for_location(self.investigator.location)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                households_list_1 = "%s\n1: %s\n2: %s\n3: %s\n4: %s\n#: Next" % (USSD.MESSAGES['HOUSEHOLD_LIST'],
                                                                                 self.hh_string(self.household_head_1),
                                                                                 self.hh_string(self.household_head_2),
                                                                                 self.hh_string(self.household_head_3),
                                                                                 self.hh_string(self.household_head_4),)
                response = self.take_survey()
                response_string = "responseString=%s&action=request" % households_list_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.respond("1")
                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % self.question_1_b.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_allows_retaking_of_house_hold_member_with_in_5min_session(self):
        self.batch.open_for_location(self.investigator.location)
        self.investigator.member_answered(self.question_1, self.household_head_1, 1, self.batch)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                response = self.select_household()

                households_member_list = "%s\n1: %s - (HEAD)" % (USSD.MESSAGES['MEMBERS_LIST'], self.household_head_1.surname)
                response_string = "responseString=%s&action=request" % households_member_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("1")
                response_string = "responseString=%s&action=request" % self.question_2.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.post_ussd_response(response='true', request_string="1")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.post_ussd_response("true", "1")
                households_member_list = "%s\n1: %s - (HEAD)*" % (USSD.MESSAGES['MEMBERS_LIST'], self.household_head_1.surname)
                response_string = "responseString=%s&action=request" % households_member_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_ussd_answers_yes_on_resume_if_investigator_dials_when_all_households_are_complete(self):
        masaka = Location.objects.create(name="Masaka")
        investigator = Investigator.objects.create(name="Another investigator",
                                                   mobile_number='779432679',
                                                   location=masaka,
                                                   backend=self.backend)
        household = Household.objects.create(investigator=investigator, location=investigator.location,
                                             uid='10', survey=self.open_survey_1)
        household_head = HouseholdHead.objects.create(household=household,
                                                      surname="Name " + str(randint(1, 9999)),
                                                      date_of_birth=datetime.date(1980, 9, 1))

        self.batch.open_for_location(investigator.location)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                self.ussd_params['msisdn'] = investigator.mobile_number
                self.take_survey()
                self.select_household()
                self.select_household_member()

                self.respond("1")
                response = self.respond("1")

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                batch_completion = household_head.household.batch_completion_batches.all()
                self.assertEqual(1, batch_completion.count())
                self.assertEqual(self.batch, batch_completion[0].batch)


                response = self.respond(USSD.ANSWER['NO'])
                response_string = "responseString=%s&action=end" % USSD.MESSAGES[
                    "SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS"]
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.reset_session()

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['YES'])

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                batch_completion = household_head.household.batch_completion_batches.all()
                self.assertEqual(1, batch_completion.count())
                self.assertEqual(self.batch, batch_completion[0].batch)

                response = self.respond(USSD.ANSWER['NO'])
                response_string = "responseString=%s&action=end" % USSD.MESSAGES[
                    "SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS"]
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_ussd_answer_no_on_resume_if_investigator_dials_when_all_households_are_complete(self):
        masaka = Location.objects.create(name="Masaka")
        investigator = Investigator.objects.create(name="Another investigator",
                                                   mobile_number='779432679',
                                                   location=masaka,
                                                   backend=self.backend)
        investigator.set_in_cache('IS_REGISTERING_HOUSEHOLD', True)
        household = Household.objects.create(investigator=investigator, location=investigator.location,
                                             uid='10', survey=self.open_survey_1)
        household_head = HouseholdHead.objects.create(household=household,
                                                      surname="Name " + str(randint(1, 9999)),
                                                      date_of_birth=datetime.date(1980, 9, 1))

        self.batch.open_for_location(investigator.location)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                self.ussd_params['msisdn'] = investigator.mobile_number
                self.take_survey()
                self.select_household()
                self.select_household_member()

                self.respond("1")
                response = self.respond("1")

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['NO'])
                response_string = "responseString=%s&action=end" % USSD.MESSAGES[
                    "SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS"]
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.reset_session()

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['NO'])

                households_member_list = "%s\n1: %s - (HEAD)*" % (USSD.MESSAGES['MEMBERS_LIST'], household_head.surname)
                response_string = "responseString=%s&action=request" % households_member_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_resume_message_if_investigator_dials_after_completing_registering_a_household(self):
        masaka = Location.objects.create(name="Masaka")
        investigator = Investigator.objects.create(name="Another investigator",
                                                   mobile_number='779432679',
                                                   location=masaka,
                                                   backend=self.backend)
        household = Household.objects.create(investigator=investigator, location=investigator.location,
                                             uid='10', survey=self.open_survey_1)
        HouseholdHead.objects.create(household=household,
                                     surname="Name " + str(randint(1, 9999)),
                                     date_of_birth=datetime.date(1980, 9, 1))
        registration_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=4)
        module = QuestionModule.objects.create(name='Registration')

        Question.objects.create(module=module, text="Please Enter the name",
                                answer_type=Question.TEXT, order=1, group=registration_group)

        Question.objects.create(module=module, text="Please Enter the age",
                                answer_type=Question.TEXT, order=2, group=registration_group)

        Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                answer_type=Question.NUMBER, order=3, group=registration_group)
        selected_household_id = '2'
        household = Household.objects.get(uid=selected_household_id)
        HouseholdHead.objects.create(household=household, surname="head_registered",
                                     date_of_birth=datetime.datetime(1980, 02, 02), male=False)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                self.ussd_params['msisdn'] = investigator.mobile_number

                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                    self.respond('1')
                    self.select_household()
                    self.respond("Name 2")
                    self.respond("20")
                    response = self.respond("1")

                with patch.object(USSDSurvey, 'is_active', return_value=True):
                    self.reset_session()
                self.respond('1')
                self.select_household()
                self.respond("Name")
                self.respond("20")
                response = self.respond("2")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), response_string)
                response = self.reset_session()
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_knows_how_to_get_questions_for_non_head_member(self):
        masaka = Location.objects.create(name="Masaka")
        investigator = Investigator.objects.create(name="Another investigator",
                                                   mobile_number='779432679',
                                                   location=masaka,
                                                   backend=self.backend)
        household = Household.objects.create(investigator=investigator, location=investigator.location,
                                             uid='10', survey=self.open_survey_1)
        household_head = HouseholdHead.objects.create(household=household,
                                                      surname="Name " + str(randint(1, 9999)),
                                                      date_of_birth=datetime.date(1980, 9, 1))
        household_member = HouseholdMember.objects.create(household=household,
                                                          surname="Member Name " + str(randint(1, 9999)),
                                                          date_of_birth=datetime.date(2010, 9, 1))

        another_member_group = HouseholdMemberGroup.objects.create(name="Less than 15", order=3)
        another_member_condition = GroupCondition.objects.create(value=15, attribute="AGE", condition="LESS_THAN")
        another_member_condition.groups.add(another_member_group)

        HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        member_question = Question.objects.create(group=self.member_group, text="Member qn",
                                                  answer_type=Question.NUMBER, order=1)
        self.batch.questions.add(member_question)
        BatchQuestionOrder.objects.create(batch=self.batch, question=member_question, order=4)

        self.batch.open_for_location(investigator.location)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                self.ussd_params['msisdn'] = investigator.mobile_number
                self.take_survey()
                self.select_household()
                self.select_household_member()

                self.respond("1")
                response = self.respond("1")

                response_string = "responseString=%s&action=request" % USSD.MESSAGES[
                    "MEMBER_SUCCESS_MESSAGE"]
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("1")

                households_member_list = "%s\n1: %s - (HEAD)*\n2: %s" % (
                    USSD.MESSAGES['MEMBERS_LIST'], household_head.surname, household_member.surname)
                response_string = "responseString=%s&action=request" % households_member_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("2")

                response_string = "responseString=%s&action=request" % self.question_3.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_retaking_of_household_member_with_in_5min_session_marks_only_that_members_responses_as_old(self):
        Household.objects.all().delete()
        household = Household.objects.create(investigator=self.investigator, location=self.investigator.location,
                                             uid=88, survey=self.open_survey_1)
        household_head = HouseholdHead.objects.create(household=household,
                                                      surname="Head 001",
                                                      date_of_birth=datetime.date(1980, 9, 1))

        household_member = HouseholdMember.objects.create(surname="Surnmae", household=household,
                                                          date_of_birth=datetime.date(2012, 2, 2), male=False)

        self.batch.open_for_location(self.investigator.location)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey_1):
                self.take_survey()
                response = self.select_household()

                households_member_list = "%s\n1: %s - (HEAD)\n2: %s" % (
                    USSD.MESSAGES['MEMBERS_LIST'], household_head.surname, household_member.surname)
                response_string = "responseString=%s&action=request" % households_member_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("1")
                response_string = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.post_ussd_response(response='true', request_string="1")
                response_string = "responseString=%s&action=request" % self.question_2.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.post_ussd_response(response='true', request_string="1")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.post_ussd_response("true", "1")
                households_member_list = "%s\n1: %s - (HEAD)*\n2: %s" % (
                    USSD.MESSAGES['MEMBERS_LIST'], household_head.surname, household_member.surname)
                response_string = "responseString=%s&action=request" % households_member_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("2")
                response_string = "responseString=%s&action=request" % self.question_3.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.post_ussd_response(response='true', request_string="1")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.post_ussd_response(response='true', request_string="1")
                households_member_list = "%s\n1: %s - (HEAD)*\n2: %s*" % (
                    USSD.MESSAGES['MEMBERS_LIST'], household_head.surname, household_member.surname)
                response_string = "responseString=%s&action=request" % households_member_list
                self.assertEquals(urllib2.unquote(response.content), response_string)
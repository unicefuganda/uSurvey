# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
from random import randint
import urllib2
from django.core.cache import cache
from django.test import Client
from mock import patch
from rapidsms.contrib.locations.models import Location, LocationType
from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Investigator, Backend, Household, HouseholdHead, Batch, HouseholdMemberGroup, NumericalAnswer, Question, TextAnswer, QuestionOption, MultiChoiceAnswer, AnswerRule, BatchQuestionOrder, GroupCondition, Survey, RandomHouseHoldSelection, EnumerationArea
from survey.models.households import HouseholdMember
from survey.tests.ussd.ussd_base_test import USSDBaseTest, FakeRequest
from survey.ussd.ussd import USSD
from survey.ussd.ussd_survey import USSDSurvey


class USSDTest(USSDBaseTest):
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
        self.household = Household.objects.create(investigator=self.investigator, location=self.investigator.location,
                                                  survey=self.open_survey, uid=0)
        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname",
                                                           date_of_birth=datetime.date(1980, 9, 1))
        self.household_1 = Household.objects.create(investigator=self.investigator, location=self.investigator.location,
                                                    survey=self.open_survey, uid=1)
        self.household_head_1 = HouseholdHead.objects.create(household=self.household_1, surname="Name " + str(randint(1, 9999)), date_of_birth=datetime.date(1980, 9, 1))
        self.household_member = HouseholdMember.objects.create(surname="Name 2", household=self.household_1,
                                                               date_of_birth=datetime.date(2000, 2, 3))
        self.batch = Batch.objects.create(order=1, name="batch test", survey=self.open_survey)
        self.batch.open_for_location(self.investigator.location)
        self.member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)

    def test_knows_can_resume_survey_if_investigator_has_open_batches_or_is_registering_households(self):
        ussd_survey = USSDSurvey(self.investigator, FakeRequest())
        self.assertTrue(ussd_survey.can_resume_survey(is_registering=False))
        self.assertTrue(ussd_survey.can_resume_survey(is_registering=True))

        self.batch.close_for_location(self.investigator.location)

        self.assertFalse(ussd_survey.can_resume_survey(is_registering=False))
        self.assertTrue(ussd_survey.can_resume_survey(is_registering=True))

    def test_list_household_members_after_selecting_household(self):
        household_member1 = HouseholdMember.objects.create(household=self.household, surname="abcd", male=False,
                                                           date_of_birth='1989-02-02')
        household_member2 = HouseholdMember.objects.create(household=self.household, surname="xyz", male=False,
                                                           date_of_birth='1989-02-02')
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                response = self.select_household()
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RETAKE_SURVEY']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond('1')

                members_list = "%s\n1: %s - (HEAD)*\n2: %s*\n3: %s*" % (
                    USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname, household_member1.surname,
                    household_member2.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_goes_back_to_household_list_if_investigator_selects_household_and_chooses_not_to_retake_survey(self):
        HouseholdMember.objects.filter(householdhead=None).delete()
        head_group = HouseholdMemberGroup.objects.create(name="General", order=1)
        condition = GroupCondition.objects.create(value='HEAD', attribute="GENERAL", condition="EQUALS")
        condition.groups.add(head_group)

        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=head_group)
        question_1.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        self.batch.open_for_location(self.investigator.location)

        self.investigator.member_answered(question_1, self.household_head, 1, self.batch)
        self.investigator.member_answered(question_1, self.household_head_1, 1, self.batch)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                response = self.select_household('2')
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RETAKE_SURVEY']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond('2')

                households_list = "%s\n1: HH-%s-%s*\n2: HH-%s-%s*" % (
                USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head.household.random_sample_number, self.household_head.surname,
                self.household_head_1.household.random_sample_number, self.household_head_1.surname)

                response_string = "responseString=%s&action=request" % households_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond('1')

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RETAKE_SURVEY']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond('1')
                members_list = "%s\n1: %s - (HEAD)*" % (
                    USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond('1')
                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_ussd_restart_survey_option_yes_with_household_set(self):
        request = FakeRequest()
        request['ussdRequestString'] = 1
        session_string = "SESSION-%s-%s" % ('1234567890', USSDSurvey.__name__)
        session = cache.get(session_string)
        session['HOUSEHOLD'] = self.household_1
        cache.set(session_string, session)

        members_list = "%s\n1: %s - (HEAD)*\n2: %s*" % (
                    USSD.MESSAGES['MEMBERS_LIST'], self.household_head_1.surname, self.household_member.surname)

        ussd_survey = USSDSurvey(self.investigator, request)
        ussd_survey.request['ussdRequestString'] = '1'


        ussd_survey.restart_survey()

        self.assertEqual(USSDSurvey.ACTIONS['REQUEST'], ussd_survey.action)
        self.assertEqual(members_list, ussd_survey.responseString)

    def test_ussd_restart_survey_option_yes_with_household_member_set(self):
        request = FakeRequest()
        request['ussdRequestString'] = 1
        session_string = "SESSION-%s-%s" % ('1234567890', USSDSurvey.__name__)
        session = cache.get(session_string)
        session['HOUSEHOLD'] = self.household_1
        session['HOUSEHOLD_MEMBER'] = self.household_member
        cache.set(session_string, session)

        restart_message = "Thank you. You have completed this household. Would you like to retake this household?\n1: Yes\n2: No"

        ussd_survey = USSDSurvey(self.investigator, request)
        ussd_survey.request['ussdRequestString'] = '1'


        ussd_survey.restart_survey()

        self.assertEqual(USSDSurvey.ACTIONS['REQUEST'], ussd_survey.action)
        self.assertEqual(restart_message, ussd_survey.responseString)

    def test_ussd_restart_survey_option_no(self):
        request = FakeRequest()
        request['ussdRequestString'] = 1
        session_string = "SESSION-%s-%s" % ('1234567890', USSDSurvey.__name__)
        session = cache.get(session_string)
        session['HOUSEHOLD'] = self.household_1
        session['HOUSEHOLD_MEMBER'] = self.household_member
        cache.set(session_string, session)

        households_list = "%s\n1: HH-%s-%s*\n2: HH-%s-%s*" % (
                USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head.household.random_sample_number, self.household_head.surname,
                self.household_head_1.household.random_sample_number, self.household_head_1.surname)

        ussd_survey = USSDSurvey(self.investigator, request)
        ussd_survey.request['ussdRequestString'] = '2'


        ussd_survey.restart_survey()

        self.assertIsNone(ussd_survey.get_from_session('HOUSEHOLD'))
        self.assertIsNone(ussd_survey.get_from_session('HOUSEHOLD_MEMBER'))
        self.assertIsNone(ussd_survey.household)
        self.assertEqual(USSDSurvey.ACTIONS['REQUEST'], ussd_survey.action)
        self.assertEqual(households_list, ussd_survey.responseString)

    def test_ussd_render_welcome_text_if_investigator_has_no_households(self):
        household_message = "Sorry, you have no households registered."
        new_investigator = Investigator.objects.create(name="new investigator",
                                                        mobile_number="001122334",
                                                        location=Location.objects.create(name="Entebbe"),
                                                        backend=Backend.objects.create(name='another'))
        ussd_survey = USSDSurvey(new_investigator, FakeRequest())
        ussd_survey.render_welcome_text()

        self.assertEqual(USSDSurvey.ACTIONS['END'], ussd_survey.action)
        self.assertEqual(household_message, ussd_survey.responseString)

    def test_end_interview_if_batch_questions_answered_more_than_time_out_minutes_ago(self):
        request = FakeRequest()
        request['ussdRequestString'] = 1
        session_string = "SESSION-%s-%s" % ('1234567890', USSDSurvey.__name__)
        session = {}
        session['HOUSEHOLD'] = self.household_1
        session['HOUSEHOLD_MEMBER'] = self.household_member
        cache.set(session_string, session)

        ussd_survey = USSDSurvey(self.investigator, request)
        ussd_survey.request['ussdRequestString'] = '1'

        with patch.object(HouseholdMember, 'survey_completed', return_value=False):
            with patch.object(HouseholdMember, 'last_question_answered', return_value=[1]):
                with patch.object(HouseholdMember, 'can_retake_survey', return_value=False):
                    ussd_survey.end_interview(self.batch)
                    self.assertEqual(USSD.MESSAGES['BATCH_5_MIN_TIMEDOUT_MESSAGE'], ussd_survey.responseString)
                    self.assertEqual(USSD.ACTIONS['END'], ussd_survey.action)

    def test_render_household_list_should_behave_like_new_request_if_no_household_selected(self):
        request = FakeRequest()
        session_string = "SESSION-%s-%s" % ('1234567890', USSDSurvey.__name__)
        session = {}
        session['HOUSEHOLD'] = self.household_1
        session['HOUSEHOLD_MEMBER'] = self.household_member
        session['PAGE'] = '1'
        cache.set(session_string, session)

        ussd_survey = USSDSurvey(self.investigator, request)
        ussd_survey.render_households_list(self.open_survey)

        self.assertEqual(USSD.ACTIONS['REQUEST'], ussd_survey.action)
        self.assertEqual(USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE'], ussd_survey.responseString)

    def test_end_interview_if_batch_questions_answered_within_time_out_minutes_ago(self):
        request = FakeRequest()
        request['ussdRequestString'] = 1
        session_string = "SESSION-%s-%s" % ('1234567890', USSDSurvey.__name__)
        session = {}
        session['HOUSEHOLD'] = self.household_1
        session['PAGE'] = '1'
        session['HOUSEHOLD_MEMBER'] = self.household_member
        cache.set(session_string, session)

        ussd_survey = USSDSurvey(self.investigator, request)
        ussd_survey.request['ussdRequestString'] = '1'

        with patch.object(HouseholdMember, 'survey_completed', return_value=False):
            with patch.object(HouseholdMember, 'can_retake_survey', return_value=True):
                ussd_survey.end_interview(self.batch)
                self.assertEqual(USSD.MESSAGES['SUCCESS_MESSAGE'], ussd_survey.responseString)
                self.assertEqual(USSD.ACTIONS['END'], ussd_survey.action)

    def test_ussd_render_welcome_text_if_investigator_has_households(self):
        homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
        welcome_message = "%s\n%s: Households list" % (homepage, USSD.HOUSEHOLD_LIST_OPTION)
        ussd_survey = USSDSurvey(self.investigator, FakeRequest())
        ussd_survey.render_welcome_text()

        self.assertEqual(USSDSurvey.ACTIONS['REQUEST'], ussd_survey.action)
        self.assertEqual(welcome_message, ussd_survey.responseString)

    def test_renders_welcome_message_if_investigator_does_not_select_option_one_or_two_from_welcome_screen(self):
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                    response = self.respond('10')
                    homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_numerical_questions(self):
        HouseholdMember.objects.create(surname="Name 2", household=self.household, date_of_birth='1980-02-03')
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                self.select_household()
                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % question_1.to_ussd()
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("4")

                self.assertEquals(4, NumericalAnswer.objects.get(investigator=self.investigator, question=question_1).answer)

                response_string = "responseString=%s&action=request" % question_2.to_ussd()
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("2")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(2, NumericalAnswer.objects.get(investigator=self.investigator, question=question_2).answer)

    def test_textual_questions(self):
        member_2 = HouseholdMember.objects.create(surname="Name 2", household=self.household,
                                                  date_of_birth='1980-02-03')
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.TEXT, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.TEXT, order=2, group=self.member_group)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                self.select_household()
                response = self.select_household_member()

                response_string = "responseString=%s&action=request" % question_1.to_ussd()
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("Reply one")

                self.assertEquals(self.ussd_params['ussdRequestString'],
                                  TextAnswer.objects.get(investigator=self.investigator, question=question_1).answer)

                response_string = "responseString=%s&action=request" % question_2.to_ussd()
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("Reply two")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(self.ussd_params['ussdRequestString'],
                                  TextAnswer.objects.get(investigator=self.investigator, question=question_2).answer)

    def test_multichoice_questions(self):
        HouseholdMember.objects.create(surname="Name 2", household=self.household, date_of_birth='1980-02-03')
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.MULTICHOICE, order=1, group=self.member_group)
        option_1_1 = QuestionOption.objects.create(question=question_1, text="OPTION 1", order=1)
        option_1_2 = QuestionOption.objects.create(question=question_1, text="OPTION 2", order=2)

        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.MULTICHOICE, order=2, group=self.member_group)
        option_2_1 = QuestionOption.objects.create(question=question_2, text="OPTION 1", order=1)
        option_2_2 = QuestionOption.objects.create(question=question_2, text="OPTION 2", order=2)

        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                self.select_household()
                response = self.select_household_member()

                response_string = "responseString=%s&action=request" % question_1.to_ussd()
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(str(option_1_1.order))
                self.assertEquals(option_1_1,
                                  MultiChoiceAnswer.objects.get(investigator=self.investigator, question=question_1).answer)

                response_string = "responseString=%s&action=request" % question_2.to_ussd()
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(str(option_2_1.order))
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(option_2_1,
                                  MultiChoiceAnswer.objects.get(investigator=self.investigator, question=question_2).answer)

    def test_multichoice_questions_pagination(self):
        question = Question.objects.create(text="This is a question",
                                           answer_type=Question.MULTICHOICE, order=1, group=self.member_group)
        option_1 = QuestionOption.objects.create(question=question, text="OPTION 1", order=1)
        option_2 = QuestionOption.objects.create(question=question, text="OPTION 2", order=2)
        option_3 = QuestionOption.objects.create(question=question, text="OPTION 3", order=3)
        option_4 = QuestionOption.objects.create(question=question, text="OPTION 4", order=4)
        option_5 = QuestionOption.objects.create(question=question, text="OPTION 5", order=5)
        option_6 = QuestionOption.objects.create(question=question, text="OPTION 6", order=6)
        option_7 = QuestionOption.objects.create(question=question, text="OPTION 7", order=7)
        back_text = Question.PREVIOUS_PAGE_TEXT
        next_text = Question.NEXT_PAGE_TEXT

        question_2 = Question.objects.create(text="This is a question",
                                             answer_type=Question.MULTICHOICE, order=2, group=self.member_group)
        option_8 = QuestionOption.objects.create(question=question_2, text="OPTION 1", order=1)
        option_9 = QuestionOption.objects.create(question=question_2, text="OPTION 2", order=2)

        question.batches.add(self.batch)
        question_2.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)

        page_1 = "%s\n1: %s\n2: %s\n3: %s\n%s" % (question.text, option_1.text, option_2.text, option_3.text, next_text)
        page_2 = "%s\n4: %s\n5: %s\n6: %s\n%s\n%s" % (
            question.text, option_4.text, option_5.text, option_6.text, back_text, next_text)
        page_3 = "%s\n7: %s\n%s" % (question.text, option_7.text, back_text)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                self.select_household()
                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % page_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("#")
                response_string = "responseString=%s&action=request" % page_2
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("#")
                response_string = "responseString=%s&action=request" % page_3
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("*")
                response_string = "responseString=%s&action=request" % page_2
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("*")
                response_string = "responseString=%s&action=request" % page_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("#")
                response_string = "responseString=%s&action=request" % page_2
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("1")
                response_string = "responseString=%s&action=request" % question_2.to_ussd()
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_reanswer_question(self):
        HouseholdMember.objects.create(surname="Name 2", household=self.household, date_of_birth='1980-02-03')
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        rule = AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['REANSWER'],
                                         condition=AnswerRule.CONDITIONS['GREATER_THAN_QUESTION'],
                                         validate_with_question=question_1)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                self.select_household()
                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("5")
                response_string = "responseString=%s&action=request" % question_2.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("10")
                response_string = "responseString=%s&action=request" % ("RECONFIRM: " + question_1.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("5")
                response_string = "responseString=%s&action=request" % ("RECONFIRM: " + question_2.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("2")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_text_invalid_answer(self):
        member_2 = HouseholdMember.objects.create(surname="Name 2", household=self.household,
                                                  date_of_birth='1980-02-03')
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.TEXT, order=1, group=self.member_group)

        question_1.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                self.select_household()

                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("")
                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + question_1.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("something")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_numerical_invalid_answer(self):
        HouseholdMember.objects.create(surname="Name 2", household=self.household, date_of_birth='1980-02-03')
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_1.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                self.select_household()
                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("a")
                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + question_1.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("2")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_multichoice_invalid_answer(self):
        HouseholdMember.objects.create(surname="Name 2", household=self.household, date_of_birth='1980-02-03')
        question_1 = Question.objects.create(text="This is a question",
                                             answer_type=Question.MULTICHOICE, order=1, group=self.member_group)
        question_1.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)

        option_1 = QuestionOption.objects.create(question=question_1, text="OPTION 1", order=1)
        option_2 = QuestionOption.objects.create(question=question_1, text="OPTION 2", order=2)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                self.select_household()

                response = self.select_household_member()
                page_1 = "%s\n1: %s\n2: %s" % (question_1.text, option_1.text, option_2.text)

                response_string = "responseString=%s&action=request" % page_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("a")
                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + page_1)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("4")
                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + page_1)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("2")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_end_interview_confirmation(self):
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)

        AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'],
                                  condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                response = self.select_household("1")

                members_list = "%s\n1: %s - (HEAD)" % (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.investigator = Investigator.objects.get(id=self.investigator.pk)

                self.assertEquals(len(self.investigator.get_from_cache('CONFIRM_END_INTERVIEW')), 0)

                response = self.select_household_member("1")
                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.investigator = Investigator.objects.get(id=self.investigator.pk)

                self.assertEquals(len(self.investigator.get_from_cache('CONFIRM_END_INTERVIEW')), 0)

                response = self.respond("0")
                response_string = "responseString=%s&action=request" % ("RECONFIRM: " + question_1.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(len(self.investigator.get_from_cache('CONFIRM_END_INTERVIEW')), 1)

                self.assertEquals(0, NumericalAnswer.objects.count())

                response = self.respond("0")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.investigator = Investigator.objects.get(id=self.investigator.pk)

                self.assertEquals(len(self.investigator.get_from_cache('CONFIRM_END_INTERVIEW')), 0)
                self.assertFalse(self.household.has_pending_survey())
                self.assertTrue(self.household_1.has_pending_survey())
                self.assertFalse(self.investigator.completed_open_surveys())

                self.set_questions_answered_to_twenty_minutes_ago()

                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                response = self.select_household("2")

                members_list = "%s\n1: %s - (HEAD)\n2: %s" % (
                    USSD.MESSAGES['MEMBERS_LIST'], self.household_head_1.surname, self.household_member.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("1")

                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                response = self.take_survey()

                households_list_1 = "%s\n1: HH-%s-%s*\n2: HH-%s-%s" % (
                        USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head.household.random_sample_number, self.household_head.surname,
                        self.household_head_1.household.random_sample_number, self.household_head_1.surname)

                response_string = "responseString=%s&action=request" % households_list_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household('1')
                members_list = "%s\n1: %s - (HEAD)*" % (
                    USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_end_interview_confirmation_alternative(self):
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)

        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)

        rule = AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'],
                                         condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                response = self.select_household()
                members_list = "%s\n1: %s - (HEAD)" % (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.investigator = Investigator.objects.get(id=self.investigator.pk)

                self.assertEquals(len(self.investigator.get_from_cache('CONFIRM_END_INTERVIEW')), 0)

                response = self.select_household_member()
                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("0")
                response_string = "responseString=%s&action=request" % ("RECONFIRM: " + question_1.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(0, NumericalAnswer.objects.count())

                response = self.respond("1")
                response_string = "responseString=%s&action=request" % question_2.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_should_show_member_completion_message_and_choose_to_go_to_member_list(self):
        member_2 = HouseholdMember.objects.create(surname="Name 2", household=self.household,
                                                  date_of_birth='1980-02-03')
        question_1 = Question.objects.create(text="Question 1?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="Question 2?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)

        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)

        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                response = self.select_household()

                members_list = "%s\n1: %s - (HEAD)\n2: %s" % (
                    USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname, member_2.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("1")
                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("1")
                response_string = "responseString=%s&action=request" % question_2.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("2")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("1")
                members_list = "%s\n1: %s - (HEAD)*\n2: %s" % (
                    USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname, member_2.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_should_show_thank_you_message_on_completion_of_all_members_questions(self):
        question_1 = Question.objects.create(text="Question 1?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="Question 2?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)

        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                response = self.select_household()

                members_list = "%s\n1: %s - (HEAD)" % (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("1")
                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("1")
                response_string = "responseString=%s&action=request" % question_2.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("2")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("2")

                households_list_1 = "%s\n1: HH-%s-%s*\n2: HH-%s-%s" % (
                USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head.household.random_sample_number, self.household_head.surname,
                self.household_head_1.household.random_sample_number, self.household_head_1.surname)

                response_string = "responseString=%s&action=request" % households_list_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_welcome_screen_should_show_message_and_options_for_registration_and_take_survey(self):
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()
                    homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_choosing_take_survey_should_render_household_list(self):
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.select_samples()

                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()
                    homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEquals(urllib2.unquote(response.content), response_string)
                    response = self.take_survey()
                    households_list_1 = "%s\n1: HH-%s-%s*\n2: HH-%s-%s*" % (
                        USSD.MESSAGES['HOUSEHOLD_LIST'], self.household_head.household.random_sample_number, self.household_head.surname,
                        self.household_head_1.household.random_sample_number, self.household_head_1.surname)
                    response_string = "responseString=%s&action=request" % households_list_1
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_choosing_registering_HH_should_set_cache(self):
        self.investigator = Investigator.objects.get(id=self.investigator.pk)
        self.batch.close_for_location(self.investigator.location)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.select_samples()

                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()

                homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                response_string = "responseString=%s&action=request" % homepage
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.register_household()

                self.assertTrue(self.investigator.get_from_cache('IS_REGISTERING_HOUSEHOLD'))

    def test_resume_should_show_welcome_text_if_open_batch_is_closed_on_session_timeout(self):
        question_1 = Question.objects.create(text="Question 1?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="Question 2?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)

        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()

                homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                response_string = "responseString=%s&action=request" % homepage
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.take_survey()
                response = self.select_household()

                members_list = "%s\n1: %s - (HEAD)" % (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                response_string = "responseString=%s&action=request" % members_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("1")
                response_string = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("1")
                response_string = "responseString=%s&action=request" % question_2.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.batch.close_for_location(self.investigator.location)

                response = self.reset_session()
                homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                response_string = "responseString=%s&action=request" % homepage
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_ussd_new_parameter_request_empty_string(self):
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))
        self.ussd_params['response'] = 'false'
        self.ussd_params['ussdRequestString'] = ''

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, "is_active", return_value=False):
                    response = self.client.post('/ussd', data=self.ussd_params)
                    homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_ussd_new_parameter_request_short_code_without_application_extension(self):
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))
        self.ussd_params['response'] = 'false'
        self.ussd_params['ussdRequestString'] = '*257#'

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, "is_active", return_value=False):
                    response = self.client.post('/ussd', data=self.ussd_params)
                    homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_ussd_new_parameter_request_short_code_with_application_extension(self):
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))
        self.ussd_params['response'] = 'false'
        self.ussd_params['ussdRequestString'] = '*153*10#'

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, "is_active", return_value=False):
                    response = self.client.post('/ussd', data=self.ussd_params)
                    homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_ussd_new_parameter_request_short_code_with_application_code_set_and_application_code_posted(self):
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))
        self.ussd_params['response'] = 'false'
        self.ussd_params['ussdRequestString'] = '10'

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, "is_active", return_value=False):
                    response = self.client.post('/ussd', data=self.ussd_params)
                    homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_subquestion_of_different_type_from_a_multichoice_parent_question_should_not_invoke_invalid_answer(self):
        HouseholdMember.objects.create(surname="Name 2", household=self.household, date_of_birth='1980-02-03')
        question_1 = Question.objects.create(text="This is a question",
                                             answer_type=Question.MULTICHOICE, order=1, group=self.member_group)
        question_1.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)

        option_1 = QuestionOption.objects.create(question=question_1, text="OPTION 1", order=1)
        option_2 = QuestionOption.objects.create(question=question_1, text="OPTION 2", order=2)
        option_3 = QuestionOption.objects.create(question=question_1, text="specify", order=3)
        sub_question_1 = Question.objects.create(text="some subquestion of question 1",
                                                 group=self.member_group,
                                                 answer_type=Question.TEXT, subquestion=True, parent=question_1)
        sub_question_1.batches.add(self.batch)
        AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                  condition=AnswerRule.CONDITIONS['EQUALS_OPTION'], validate_with_option=option_3,
                                  next_question=sub_question_1)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()

                self.take_survey()
                self.select_household()

                response = self.select_household_member()
                page_1 = "%s\n1: %s\n2: %s\n3: %s" % (question_1.text, option_1.text, option_2.text, option_3.text)

                response_string = "responseString=%s&action=request" % page_1
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("3")
                response_string = "responseString=%s&action=request" % (sub_question_1.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)
                self.assertNotIn("INVALID ANSWER", urllib2.unquote(response.content))
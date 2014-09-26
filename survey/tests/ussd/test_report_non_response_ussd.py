from random import randint
import datetime
import urllib2

from mock import patch
from django.test import Client
from rapidsms.contrib.locations.models import Location

from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Backend, Survey, Investigator, Household, Batch, RandomHouseHoldSelection, QuestionModule, HouseholdMemberGroup, QuestionOption, Question, HouseholdHead, MultiChoiceAnswer, HouseholdMember, GroupCondition, BatchQuestionOrder, NumericalAnswer, EnumerationArea
from survey.tests.ussd.ussd_base_test import USSDBaseTest
from survey.ussd.ussd import USSD
from survey.ussd.ussd_report_non_response import USSDReportNonResponse
from survey.ussd.ussd_survey import USSDSurvey


class USSDReportingNonResponseTest(USSDBaseTest):
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

        self.ea = EnumerationArea.objects.create(name="EA2", survey=self.open_survey)
        self.ea.locations.add(self.kampala)

        self.batch.open_for_location(self.kampala)

        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number=self.ussd_params['msisdn'].replace(
                                                            COUNTRY_PHONE_CODE, '', 1), ea=self.ea, backend=self.backend)

        self.household1 = self.create_household(1)
        self.household2 = self.create_household(2)
        self.household3 = self.create_household(3)
        self.household4 = self.create_household(4)

        self.household_head = self.create_household_member(name="Bob", household=self.household1)
        self.household_head2 = self.create_household_member(name="Bob 2 Head", household=self.household2)
        self.household_head3 = self.create_household_member(name="Bob 3 Head", household=self.household3)
        self.household_head4 = self.create_household_member(name="Bob 4 Head", household=self.household4)

        self.none_response_group = HouseholdMemberGroup.objects.create(name="NON_RESPONSE", order=0)
        module = QuestionModule.objects.create(name='NON RESPONSE')
        self.non_response_question = Question.objects.create(module=module,
                                                             text="Why did HH-%s-%s not take the survey",
                                                             answer_type=Question.MULTICHOICE, order=1,
                                                             group=self.none_response_group)
        QuestionOption.objects.create(question=self.non_response_question, text="House closed", order=1)
        QuestionOption.objects.create(question=self.non_response_question, text="Household moved", order=2)
        QuestionOption.objects.create(question=self.non_response_question, text="Refused to answer", order=3)
        QuestionOption.objects.create(question=self.non_response_question, text="Died", order=4)

        self.member_non_response_question = Question.objects.create(module=module,
                                                                    text="Why did %s not take the survey",
                                                                    answer_type=Question.MULTICHOICE, order=2,
                                                                    group=self.none_response_group)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Member Refused", order=1)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason", order=2)

        self.registration_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                      order=1)
        self.module = QuestionModule.objects.create(name='Registration')
        self.question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                                  answer_type=Question.TEXT, order=1, group=self.registration_group)
        self.age_question = Question.objects.create(module=module, text="Please Enter the age",
                                                    answer_type=Question.NUMBER, order=2, group=self.registration_group)
        self.month_question = Question.objects.create(module=module, text="Please Enter the month of birth",
                                                      answer_type=Question.MULTICHOICE, order=3,
                                                      group=self.registration_group)
        QuestionOption.objects.create(question=self.month_question, text="January", order=1)
        QuestionOption.objects.create(question=self.month_question, text="February", order=2)
        QuestionOption.objects.create(question=self.month_question, text="March", order=3)
        QuestionOption.objects.create(question=self.month_question, text="April", order=4)
        QuestionOption.objects.create(question=self.month_question, text="May", order=5)
        QuestionOption.objects.create(question=self.month_question, text="June", order=6)
        QuestionOption.objects.create(question=self.month_question, text="July", order=7)
        QuestionOption.objects.create(question=self.month_question, text="August", order=8)
        QuestionOption.objects.create(question=self.month_question, text="September", order=9)
        QuestionOption.objects.create(question=self.month_question, text="October", order=10)
        QuestionOption.objects.create(question=self.month_question, text="November", order=11)
        QuestionOption.objects.create(question=self.month_question, text="December", order=12)
        QuestionOption.objects.create(question=self.month_question, text="DONT KNOW", order=99)

        self.year_question = Question.objects.create(module=module, text="Please Enter the year of birth",
                                                     answer_type=Question.NUMBER, order=4,
                                                     group=self.registration_group)
        self.gender_question = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                                       answer_type=Question.NUMBER, order=5,
                                                       group=self.registration_group)

        head_group = HouseholdMemberGroup.objects.create(name="General", order=2)
        condition = GroupCondition.objects.create(value='HEAD', attribute="GENERAL", condition="EQUALS")
        condition.groups.add(head_group)

        self.question_1 = Question.objects.create(text="Question 1",
                                                  answer_type=Question.NUMBER, order=0, group=head_group)
        self.question_1.batches.add(self.batch)
        BatchQuestionOrder.objects.create(batch=self.batch, question=self.question_1, order=1)

    def create_household(self, unique_id):
        return Household.objects.create(investigator=self.investigator, ea=self.investigator.ea,
                                        uid=unique_id, random_sample_number=unique_id, survey=self.open_survey)

    def create_household_member(self, name, household, head=True, date_of_birth="1990-9-9", minutes_ago=6):
        object_to_create = HouseholdHead if head else HouseholdMember
        household_member = object_to_create.objects.create(surname=name, date_of_birth=date_of_birth,
                                                           household=household)
        household_member.created -= datetime.timedelta(minutes=minutes_ago)
        household_member.save()
        return household_member

    def test_shows_non_response_menu_if_its_activated_and_there_are_HH_who_qualify_for_NR_questions(self):
        self.batch.activate_non_response_for(self.kampala)
        self.investigator.batch_completion_completed_households.all().delete()
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

    def test_does_not_show_non_response_menu_if_no_HH_qualify_for_NR_questions_even_if_activated(self):
        self.batch.activate_non_response_for(self.kampala)
        self.household1.batch_completed(self.batch)
        self.household2.batch_completed(self.batch)
        self.household3.batch_completed(self.batch)
        self.household4.batch_completed(self.batch)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    response = self.reset_session()
                    homepage = "Welcome %s to the survey.\n1: Register households\n2: Take survey" % self.investigator.name
                    response_string = "responseString=%s&action=request" % homepage
                    self.assertEqual(urllib2.unquote(response.content), response_string)

    def test_shows_only_REGISTERED_households_that_have_not_completed(self):
        self.household1.batch_completed(self.batch)
        self.household2.batch_completed(self.batch)

        self.household_head3.delete()

        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                    response = self.choose_menu_to_report_non_response()
                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s" % \
                                     (self.household4.uid, self.household_head4.surname)
                    first_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)

    def test_paginates_non_completed_households_list(self):
        household5 = self.create_household(5)
        household6 = self.create_household(6)
        household7 = self.create_household(7)
        household8 = self.create_household(8)
        household9 = self.create_household(9)
        household10 = self.create_household(10)

        household_head5 = self.create_household_member(name="Bob 5 Head", household=household5)
        household_head6 = self.create_household_member(name="Bob 6 Head", household=household6)
        household_head7 = self.create_household_member(name="Bob 7 Head", household=household7)
        household_head8 = self.create_household_member(name="Bob 8 Head", household=household8)
        household_head9 = self.create_household_member(name="Bob 9 Head", household=household9)
        household_head10 = self.create_household_member(name="Bob 10 Head", household=household10)

        self.household1.batch_completed(self.batch)

        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                    response = self.choose_menu_to_report_non_response()
                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s" \
                                                                       "\n2: HH-%s-%s" \
                                                                       "\n3: HH-%s-%s" \
                                                                       "\n4: HH-%s-%s" \
                                                                       "\n#: Next" % (
                                         self.household2.uid, self.household_head2.surname,
                                         self.household3.uid, self.household_head3.surname,
                                         self.household4.uid, self.household_head4.surname,
                                         household5.uid, household_head5.surname)
                    first_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)
                    response = self.respond("#")

                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n5: HH-%s-%s" \
                                                                       "\n6: HH-%s-%s" \
                                                                       "\n7: HH-%s-%s" \
                                                                       "\n8: HH-%s-%s" \
                                                                       "\n*: Back\n#: Next" % (
                                         household6.uid, household_head6.surname,
                                         household7.uid, household_head7.surname,
                                         household8.uid, household_head8.surname,
                                         household9.uid, household_head9.surname)
                    second_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), second_page_list)

                    response = self.respond("#")

                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n9: HH-%s-%s\n*: Back" \
                                     % (household10.uid, household_head10.surname)
                    last_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), last_page_list)

                    response = self.respond("*")
                    self.assertEquals(urllib2.unquote(response.content), second_page_list)

                    response = self.respond("*")
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)

    def test_shows_non_response_questions_for_non_completed_households_if_none_of_the_members_have_completed_the_survey(
            self):
        household_member = self.create_household_member(name="bob son", household=self.household1, head=False,
                                                        date_of_birth="1996-9-9")
        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    response = self.select_household()
                    non_response_option_page = "\n1: House closed\n2: Household moved\n3: Refused to answer\n#: Next"
                    question_and_options = self.non_response_question.text % (
                        self.household1.uid, self.household_head.surname) + non_response_option_page
                    non_response_question = "responseString=%s&action=request" % question_and_options
                    self.assertEquals(urllib2.unquote(response.content), non_response_question)

    def test_paginates_households_non_response_questions_options(self):
        household_member = self.create_household_member(name="bob son", household=self.household1, head=False,
                                                        date_of_birth="1996-9-9")
        self.batch.activate_non_response_for(self.kampala)
        QuestionOption.objects.create(question=self.non_response_question, text="Reason 5", order=5)
        QuestionOption.objects.create(question=self.non_response_question, text="Reason 6", order=6)
        QuestionOption.objects.create(question=self.non_response_question, text="Reason 7", order=7)
        QuestionOption.objects.create(question=self.non_response_question, text="Reason 8", order=8)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, 'is_active', return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    response = self.select_household()
                    non_response_option_page_1 = "\n1: House closed\n2: Household moved\n3: Refused to answer\n#: Next"
                    question_and_options_page_1 = self.non_response_question.text % (
                        self.household1.uid, self.household_head.surname) + non_response_option_page_1
                    non_response_question_page_1 = "responseString=%s&action=request" % question_and_options_page_1
                    self.assertEquals(urllib2.unquote(response.content), non_response_question_page_1)

                    response = self.respond("#")
                    non_response_option_page_2 = "\n4: Died\n5: Reason 5\n6: Reason 6\n*: Back\n#: Next"
                    question_and_options_page_2 = self.non_response_question.text % (
                        self.household1.uid, self.household_head.surname) + non_response_option_page_2
                    non_response_question_page_2 = "responseString=%s&action=request" % question_and_options_page_2
                    self.assertEquals(urllib2.unquote(response.content), non_response_question_page_2)

                    invalid_option = '456'
                    response = self.respond(invalid_option)
                    invalid_page_2 = "responseString=%s&action=request" % (
                        "INVALID ANSWER: " + question_and_options_page_2)
                    self.assertEquals(urllib2.unquote(response.content), invalid_page_2)

                    invalid_option = 'blabliblofkajf89748u2&^^%%^&*'
                    response = self.respond(invalid_option)
                    invalid_page_2 = "responseString=%s&action=request" % (
                        "INVALID ANSWER: " + question_and_options_page_2)
                    self.assertEquals(urllib2.unquote(response.content), invalid_page_2)

                    response = self.respond("#")
                    non_response_option_page_3 = "\n7: Reason 7\n8: Reason 8\n*: Back"
                    question_and_options_page_3 = self.non_response_question.text % (
                        self.household1.uid, self.household_head.surname) + non_response_option_page_3
                    non_response_question = "responseString=%s&action=request" % question_and_options_page_3
                    self.assertEquals(urllib2.unquote(response.content), non_response_question)

                    response = self.respond("*")
                    self.assertEquals(urllib2.unquote(response.content), non_response_question_page_2)

                    response = self.respond("*")
                    self.assertEquals(urllib2.unquote(response.content), non_response_question_page_1)

    def test_saves_households_non_response_question_answers_and_show_non_complete_household_list_again_with_stars(self):
        household_member = self.create_household_member(name="bob son", household=self.household1, head=False,
                                                        date_of_birth="1996-9-9")

        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                self.select_household()
                response = self.respond("2")
                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s*\n2: HH-%s-%s" \
                                                                   "\n3: HH-%s-%s\n4: HH-%s-%s" \
                                 % (self.household1.uid, self.household_head.surname,
                                    self.household2.uid, self.household_head2.surname,
                                    self.household3.uid, self.household_head3.surname,
                                    self.household4.uid, self.household_head4.surname)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

                self.assertEquals(2, MultiChoiceAnswer.objects.get(investigator=self.investigator, batch=self.batch,
                                                                   question=self.non_response_question,
                                                                   household=self.household1).answer.order)

    def test_shows_household_members_who_did_not_complete_when_household_is_selected(self):
        self.batch.activate_non_response_for(self.kampala)

        household_member = self.create_household_member(name="bob son", household=self.household1, head=False,
                                                        date_of_birth="1996-9-9")
        household_member_who_completed = self.create_household_member(name="bob good son", household=self.household1,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                response = self.select_household()
                households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname,
                                          household_member.surname)
                expected_screen = "%s\n1: %s - (respondent)\n2: %s" % households_member_list
                response_string = "responseString=%s&action=request" % expected_screen
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_paginates_list_of_household_members_who_did_not_complete_when_household_is_selected(self):
        household_member_who_completed = self.create_household_member(name="bob good son", household=self.household1,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        self.batch.activate_non_response_for(self.kampala)

        household_member1 = self.create_household_member(name="bob1", household=self.household1, head=False,
                                                         date_of_birth="1996-9-9")
        household_member2 = self.create_household_member(name="bob2", household=self.household1, head=False,
                                                         date_of_birth="1996-9-10")
        household_member3 = self.create_household_member(name="bob3", household=self.household1, head=False,
                                                         date_of_birth="1996-9-11")
        household_member4 = self.create_household_member(name="bob4", household=self.household1, head=False,
                                                         date_of_birth="1996-9-12")
        household_member5 = self.create_household_member(name="bob5", household=self.household1, head=False,
                                                         date_of_birth="1996-9-13")
        household_member6 = self.create_household_member(name="bob6", household=self.household1, head=False,
                                                         date_of_birth="1996-9-14")
        household_member7 = self.create_household_member(name="bob7", household=self.household1, head=False,
                                                         date_of_birth="1996-9-15")
        household_member8 = self.create_household_member(name="bob8", household=self.household1, head=False,
                                                         date_of_birth="1996-9-16")

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                response = self.select_household()
                households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname,
                                          household_member1.surname, household_member2.surname,
                                          household_member3.surname)
                expected_screen_page_1 = "%s\n1: %s - (respondent)\n2: %s\n3: %s\n4: %s\n#: Next" % households_member_list
                member_list_page_1 = "responseString=%s&action=request" % expected_screen_page_1
                self.assertEquals(urllib2.unquote(response.content), member_list_page_1)

                response = self.respond("#")
                households_member_list = (
                    USSD.MESSAGES['MEMBERS_LIST'], household_member4.surname, household_member5.surname,
                    household_member6.surname, household_member7.surname)
                expected_screen_page_2 = "%s\n5: %s\n6: %s\n7: %s\n8: %s\n*: Back\n#: Next" % households_member_list
                member_list_page_2 = "responseString=%s&action=request" % expected_screen_page_2
                self.assertEquals(urllib2.unquote(response.content), member_list_page_2)

                invalid_option = '456'
                response = self.respond(invalid_option)
                invalid_page_2 = "responseString=%s&action=request" % (
                    "INVALID SELECTION: " + expected_screen_page_2)
                self.assertEquals(urllib2.unquote(response.content), invalid_page_2)

                invalid_option = 'blabliblofkajf89748u2&^^%%^&*'
                response = self.respond(invalid_option)
                invalid_page_2 = "responseString=%s&action=request" % (
                    "INVALID SELECTION: " + expected_screen_page_2)
                self.assertEquals(urllib2.unquote(response.content), invalid_page_2)

                response = self.respond("#")
                households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], household_member8.surname)
                expected_screen_page_3 = "%s\n9: %s\n*: Back" % households_member_list
                member_list_page_3 = "responseString=%s&action=request" % expected_screen_page_3
                self.assertEquals(urllib2.unquote(response.content), member_list_page_3)

                response = self.respond("*")
                self.assertEquals(urllib2.unquote(response.content), member_list_page_2)

                response = self.respond("*")
                self.assertEquals(urllib2.unquote(response.content), member_list_page_1)

    def test_should_not_show_household_members_who_completed_when_household_is_selected(self):
        self.batch.activate_non_response_for(self.kampala)

        household_member = self.create_household_member(name="bob son", household=self.household1, head=False,
                                                        date_of_birth="1996-9-9")
        household_member.batch_completed(self.batch)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                response = self.select_household()
                households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                expected_screen = "%s\n1: %s - (respondent)" % households_member_list
                response_string = "responseString=%s&action=request" % expected_screen
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_should_show_household_members_non_response_question_when_member_is_selected(self):
        self.batch.activate_non_response_for(self.kampala)

        household_member_who_completed = self.create_household_member(name="bob good son", household=self.household1,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                self.select_household()
                response = self.select_household_member()
                non_response_option_page = "\n1: Member Refused\n2: Reason"
                question_and_options = self.member_non_response_question.text % self.household_head.surname + non_response_option_page
                non_response_question = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

    def test_should_paginate_household_members_non_response_question_options(self):
        self.batch.activate_non_response_for(self.kampala)
        household_member_who_completed = self.create_household_member(name="bob good son", household=self.household1,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 2", order=3)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 3", order=4)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 4", order=5)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 5", order=6)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 6", order=7)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 7", order=8)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 8", order=9)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                self.select_household()
                response = self.select_household_member()
                non_response_option_page = "\n1: Member Refused\n2: Reason\n3: Reason 2\n#: Next"
                question_and_options = self.member_non_response_question.text % self.household_head.surname + non_response_option_page
                non_response_question_page_1 = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question_page_1)

                response = self.respond("#")
                non_response_option_page_2 = "\n4: Reason 3\n5: Reason 4\n6: Reason 5\n*: Back\n#: Next"
                question_and_options_page_2 = self.member_non_response_question.text % self.household_head.surname + non_response_option_page_2
                non_response_question_page_2 = "responseString=%s&action=request" % question_and_options_page_2
                self.assertEquals(urllib2.unquote(response.content), non_response_question_page_2)

                invalid_option = '456'
                response = self.respond(invalid_option)
                invalid_page_2 = "responseString=%s&action=request" % (
                    "INVALID ANSWER: " + question_and_options_page_2)
                self.assertEquals(urllib2.unquote(response.content), invalid_page_2)

                invalid_option = 'blabliblofkajf89748u2&^^%%^&*'
                response = self.respond(invalid_option)
                invalid_page_2 = "responseString=%s&action=request" % (
                    "INVALID ANSWER: " + question_and_options_page_2)
                self.assertEquals(urllib2.unquote(response.content), invalid_page_2)

                response = self.respond("#")
                non_response_option_page_3 = "\n7: Reason 6\n8: Reason 7\n9: Reason 8\n*: Back"
                question_and_options_page_3 = self.member_non_response_question.text % self.household_head.surname + non_response_option_page_3
                non_response_question = "responseString=%s&action=request" % question_and_options_page_3
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

                response = self.respond("*")
                self.assertEquals(urllib2.unquote(response.content), non_response_question_page_2)

                response = self.respond("*")
                self.assertEquals(urllib2.unquote(response.content), non_response_question_page_1)

    def test_saves_households_member_non_response_question_answers_and_shows_the_members_again_with_stars(self):
        household_member = self.create_household_member(name="bob son", household=self.household1, head=False,
                                                        date_of_birth="1996-9-9")
        household_member_who_completed = self.create_household_member(name="bob good son", household=self.household1,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                self.select_household()
                self.select_household_member()
                response = self.respond("1")

                households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname,
                                          household_member.surname)
                expected_screen = "%s\n1: %s - (respondent)*\n2: %s" % households_member_list
                response_string = "responseString=%s&action=request" % expected_screen
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(1, MultiChoiceAnswer.objects.get(investigator=self.investigator, batch=self.batch,
                                                                   question=self.member_non_response_question,
                                                                   household=self.household1,
                                                                   householdmember=self.household_head).answer.order)

    def test_should_show_non_response_of_next_member_with_his_name_when_a_member_has_finished_and_next_one_chosen(self):
        household_member = self.create_household_member(name="bob son", household=self.household1, head=False,
                                                        date_of_birth="1996-9-9")
        household_member_who_completed = self.create_household_member(name="bob good son", household=self.household1,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                self.select_household()
                self.select_household_member()
                self.respond("1")
                response = self.select_household_member("2")
                non_response_option_page = "\n1: Member Refused\n2: Reason"
                question_and_options = self.member_non_response_question.text % household_member.surname + non_response_option_page
                non_response_question = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

    def test_shows_household_list_after_all_households_members_for_a_household_all_have_finished_and_shows_stars(self):
        household_member = self.create_household_member(name="bob son", household=self.household1, head=False,
                                                        date_of_birth="1996-9-9")
        household_member_who_completed = self.create_household_member(name="bob good son", household=self.household1,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                self.select_household()
                self.select_household_member()
                self.respond("1")
                self.select_household_member("2")
                response = self.respond("1")

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s*\n2: HH-%s-%s" \
                                                                   "\n3: HH-%s-%s\n4: HH-%s-%s" \
                                 % (self.household1.uid, self.household_head.surname,
                                    self.household2.uid, self.household_head2.surname,
                                    self.household3.uid, self.household_head3.surname,
                                    self.household4.uid, self.household_head4.surname)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

    def test_shows_non_response_completion_message_upon_completion_of_all_households_when_last_household_has_household_non_response_question(
            self):
        self.batch.activate_non_response_for(self.kampala)
        answer_dict = {'investigator': self.investigator, 'question': self.non_response_question, 'batch': self.batch}
        MultiChoiceAnswer.objects.create(household=self.household1, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household2, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household3, **answer_dict)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    self.select_household("4")
                    response = self.respond("1")
                    response_string = "responseString=%s&action=request" % USSD.MESSAGES['NON_RESPONSE_COMPLETION']
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_shows_non_response_completion_message_upon_completion_of_all_households_when_last_household_has_member_non_response_question(
            self):
        self.batch.activate_non_response_for(self.kampala)
        answer_dict = {'investigator': self.investigator, 'question': self.non_response_question, 'batch': self.batch}
        MultiChoiceAnswer.objects.create(household=self.household1, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household2, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household3, **answer_dict)

        household_member_who_completed = self.create_household_member(name="bob4 good son", household=self.household4,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    self.select_household("4")
                    self.select_household_member("1")
                    response = self.respond("1")
                    response_string = "responseString=%s&action=request" % USSD.MESSAGES['NON_RESPONSE_COMPLETION']
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_shows_HH_list_with_stars_if_responding_yes_to_non_response_completion_message_transtion_from_HH_non_response_question(
            self):
        self.batch.activate_non_response_for(self.kampala)
        answer_dict = {'investigator': self.investigator, 'question': self.non_response_question, 'batch': self.batch}
        MultiChoiceAnswer.objects.create(household=self.household1, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household2, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household3, **answer_dict)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    self.select_household("4")
                    self.respond("1")
                    response = self.respond(USSDReportNonResponse.ANSWER['IS_RETAKING'])
                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s*\n2: HH-%s-%s*" \
                                                                       "\n3: HH-%s-%s*\n4: HH-%s-%s*" \
                                     % (self.household1.uid, self.household_head.surname,
                                        self.household2.uid, self.household_head2.surname,
                                        self.household3.uid, self.household_head3.surname,
                                        self.household4.uid, self.household_head4.surname)
                    first_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)

    def test_shows_HH_list_with_stars_if_responding_yes_to_non_response_completion_message_transtion_from_member_non_response_question(
            self):
        self.batch.activate_non_response_for(self.kampala)
        answer_dict = {'investigator': self.investigator, 'question': self.non_response_question, 'batch': self.batch}
        MultiChoiceAnswer.objects.create(household=self.household1, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household2, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household3, **answer_dict)

        household_member_who_completed = self.create_household_member(name="bob4 good son", household=self.household4,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    self.select_household("4")
                    self.select_household_member("1")
                    self.respond("1")

                    response = self.respond(USSDReportNonResponse.ANSWER['IS_RETAKING'])
                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s*\n2: HH-%s-%s*" \
                                                                       "\n3: HH-%s-%s*\n4: HH-%s-%s*" \
                                     % (self.household1.uid, self.household_head.surname,
                                        self.household2.uid, self.household_head2.surname,
                                        self.household3.uid, self.household_head3.surname,
                                        self.household4.uid, self.household_head4.surname)
                    first_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)

    def test_shows_hh_non_response_questions_after_selecting_hh_transition_from_non_response_completion_message(self):
        self.batch.activate_non_response_for(self.kampala)
        answer_dict = {'investigator': self.investigator, 'question': self.non_response_question, 'batch': self.batch}
        MultiChoiceAnswer.objects.create(household=self.household1, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household2, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household3, **answer_dict)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    self.select_household("4")
                    self.respond("1")
                    self.respond(USSDReportNonResponse.ANSWER['IS_RETAKING'])
                    response = self.select_household("1")
                    non_response_option_page = "\n1: House closed\n2: Household moved\n3: Refused to answer\n#: Next"
                    question_and_options = self.non_response_question.text % (
                        self.household1.uid, self.household_head.surname) + non_response_option_page
                    non_response_question = "responseString=%s&action=request" % question_and_options
                    self.assertEquals(urllib2.unquote(response.content), non_response_question)

    def test_shows_member_non_response_questions_after_selecting_member_transition_from_non_response_completion_message(
            self):
        self.batch.activate_non_response_for(self.kampala)
        answer_dict = {'investigator': self.investigator, 'question': self.non_response_question, 'batch': self.batch}
        MultiChoiceAnswer.objects.create(household=self.household1, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household2, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household3, **answer_dict)

        household_member_who_completed = self.create_household_member(name="bob4 good son", household=self.household4,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    self.select_household("4")
                    self.select_household_member("1")
                    self.respond("1")
                    self.respond(USSDReportNonResponse.ANSWER['IS_RETAKING'])
                    self.select_household("4")
                    response = self.select_household_member("1")
                    non_response_option_page = "\n1: Member Refused\n2: Reason"
                    question_and_options = self.member_non_response_question.text % self.household_head4.surname + \
                        non_response_option_page
                    non_response_question = "responseString=%s&action=request" % question_and_options
                    self.assertEquals(urllib2.unquote(response.content), non_response_question)

    def test_shows_welcome_menu_if_responding_no_to_non_response_completion_message(self):
        self.batch.activate_non_response_for(self.kampala)
        answer_dict = {'investigator': self.investigator, 'question': self.non_response_question, 'batch': self.batch}
        MultiChoiceAnswer.objects.create(household=self.household1, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household2, **answer_dict)
        MultiChoiceAnswer.objects.create(household=self.household3, **answer_dict)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                self.select_household("4")
                self.respond("1")
                response = self.respond(USSD.ANSWER['NO'])
                homepage = "Welcome %s to the survey.\n1:" \
                           " Register households\n2: " \
                           "Take survey\n3: " \
                           "Report non-response" % self.investigator.name
                response_string = "responseString=%s&action=request" % homepage
                self.assertEqual(urllib2.unquote(response.content), response_string)

    def test_flow_from_non_response_to_take_survey(self):
        self.batch.activate_non_response_for(self.kampala)

        self.household2.delete()
        self.household3.delete()
        self.household4.delete()

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    self.select_household("1")
                    self.respond("1")
                    self.respond(USSD.ANSWER['NO'])
                    response = self.respond(USSD.ANSWER['TAKE_SURVEY'])

                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s" \
                                     % (self.household1.uid, self.household_head.surname)
                    first_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)

                    response = self.select_household("1")
                    households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                    expected_screen = "%s\n1: %s - (respondent)" % households_member_list
                    response_string = "responseString=%s&action=request" % expected_screen
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                    response = self.select_household_member("1")
                    response_string = "responseString=%s&action=request" % self.question_1.text
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                    response = self.respond("3")
                    response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                    self.assertEquals(3, NumericalAnswer.objects.get(investigator=self.investigator,
                                                                     question=self.question_1,
                                                                     household=self.household1).answer)

                    response = self.respond(USSD.ANSWER['NO'])
                    response_string = "responseString=%s&action=end" % USSD.MESSAGES[
                        'SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS']
                    self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_flow_from_non_response_to_register_household(self):
        self.batch.activate_non_response_for(self.kampala)

        self.household2.delete()
        self.household3.delete()
        self.household4.delete()

        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age}

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                    self.choose_menu_to_report_non_response()
                    self.select_household("1")
                    self.respond("1")
                    self.respond(USSD.ANSWER['NO'])

                    self.household2 = self.create_household(2)

                    response = self.respond(USSD.ANSWER['REGISTER_HOUSEHOLD'])

                    household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s\n2: HH-%s" \
                                     % (self.household1.uid, self.household_head.surname, self.household2.uid)
                    first_page_list = "responseString=%s&action=request" % household_list
                    self.assertEquals(urllib2.unquote(response.content), first_page_list)

                    response = self.select_household("2")
                    select_member_or_head = USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % self.household2.uid
                    response_string = "responseString=%s&action=request" % select_member_or_head
                    self.assertEquals(urllib2.unquote(response.content), response_string)

                    self.respond('1')
                    self.respond(answers['name'])
                    self.respond(answers['age'])
                    self.respond(answers['month'])
                    self.respond(answers['year'])
                    response = self.respond(answers['gender'])
                    end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                    self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                    self.assertEqual(1, self.household2.household_member.count())
                    member = self.household2.household_member.all()[0]
                    self.assertEqual(member.surname, answers['name'])
                    self.assertEqual(member.male, True)

    def test_pagination_on_one_side_is_not_inherited_in_pagination_on_other_sides(self):
        household_member_who_completed = self.create_household_member(name="bob good son", household=self.household1,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        self.batch.activate_non_response_for(self.kampala)

        household5 = self.create_household(5)
        household6 = self.create_household(6)
        household7 = self.create_household(7)
        household8 = self.create_household(8)
        household9 = self.create_household(9)
        household10 = self.create_household(10)

        self.create_household_member(name="Bob 5 Head", household=household5)
        household_head6 = self.create_household_member(name="Bob 6 Head", household=household6)
        household_head7 = self.create_household_member(name="Bob 7 Head", household=household7)
        self.create_household_member(name="Bob 8 Head", household=household8)
        self.create_household_member(name="Bob 9 Head", household=household9)
        self.create_household_member(name="Bob 10 Head", household=household10)

        household_member1 = self.create_household_member(name="bob1", household=household7, head=False,
                                                         date_of_birth="1996-9-9")
        household_member2 = self.create_household_member(name="bob2", household=household7, head=False,
                                                         date_of_birth="1996-9-10")
        household_member3 = self.create_household_member(name="bob3", household=household7, head=False,
                                                         date_of_birth="1996-9-11")
        household_member4 = self.create_household_member(name="bob4", household=household7, head=False,
                                                         date_of_birth="1996-9-12")
        household_member5 = self.create_household_member(name="bob5", household=household7, head=False,
                                                         date_of_birth="1996-9-13")
        household_member6 = self.create_household_member(name="bob6", household=household7, head=False,
                                                         date_of_birth="1996-9-14")
        household_member7 = self.create_household_member(name="bob7", household=household7, head=False,
                                                         date_of_birth="1996-9-15")
        household_member8 = self.create_household_member(name="bob8", household=household7, head=False,
                                                         date_of_birth="1996-9-16")

        household_member_who_completed = self.create_household_member(name="bob good son", household=household7,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 2", order=3)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 3", order=4)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 4", order=5)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 5", order=6)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 6", order=7)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 7", order=8)
        QuestionOption.objects.create(question=self.member_non_response_question, text="Reason 8", order=9)

        QuestionOption.objects.create(question=self.non_response_question, text="Reason 5", order=5)
        QuestionOption.objects.create(question=self.non_response_question, text="Reason 6", order=6)
        QuestionOption.objects.create(question=self.non_response_question, text="Reason 7", order=7)
        QuestionOption.objects.create(question=self.non_response_question, text="Reason 8", order=8)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                response = self.choose_menu_to_report_non_response()

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s" \
                                                                   "\n2: HH-%s-%s" \
                                                                   "\n3: HH-%s-%s" \
                                                                   "\n4: HH-%s-%s" \
                                                                   "\n#: Next" % (
                                     self.household1.uid, self.household_head.surname,
                                     self.household2.uid, self.household_head2.surname,
                                     self.household3.uid, self.household_head3.surname,
                                     self.household4.uid, self.household_head4.surname)
                HH_list_page_1 = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), HH_list_page_1)

                self.respond("#")
                response = self.respond("7")

                households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], household_head7.surname,
                                          household_member1.surname, household_member2.surname,
                                          household_member3.surname)
                member_list_page_1 = "%s\n1: %s - (respondent)\n2: %s\n3: %s\n4: %s\n#: Next" % households_member_list
                formatted_member_list_page_1 = "responseString=%s&action=request" % member_list_page_1
                self.assertEquals(urllib2.unquote(response.content), formatted_member_list_page_1)

                self.respond("#")
                response = self.respond("5")

                non_response_option_page = "\n1: Member Refused\n2: Reason\n3: Reason 2\n#: Next"
                question_and_options = self.member_non_response_question.text % household_member4.surname + non_response_option_page
                non_response_question_page_1 = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question_page_1)

                self.respond("#")
                response = self.respond("4")
                self.assertEquals(urllib2.unquote(response.content), formatted_member_list_page_1)

                self.respond("#")
                response = self.respond("6")
                question_and_options = self.member_non_response_question.text % household_member5.surname + non_response_option_page
                non_response_question_page_1 = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question_page_1)

                household_member1.delete()
                household_member2.delete()
                household_member3.delete()
                household_member6.delete()
                household_member7.delete()
                household_member8.delete()
                household_head7.delete()

                self.respond("#")
                response = self.respond("5")
                self.assertEquals(urllib2.unquote(response.content), HH_list_page_1)

                self.respond("#")
                response = self.respond("6")
                non_response_option_page_1 = "\n1: House closed\n2: Household moved\n3: Refused to answer\n#: Next"
                question_and_options_page_1 = self.non_response_question.text % (
                    household6.uid, household_head6.surname) + non_response_option_page_1
                non_response_question_page_1 = "responseString=%s&action=request" % question_and_options_page_1
                self.assertEquals(urllib2.unquote(response.content), non_response_question_page_1)

    def test_resume_from_non_response_to_take_survey(self):
        self.batch.activate_non_response_for(self.kampala)

        self.household2.delete()
        self.household3.delete()
        self.household4.delete()
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                self.choose_menu_to_report_non_response()
                response = self.select_household("1")
                non_response_option_page = "\n1: House closed\n2: Household moved\n3: Refused to answer\n#: Next"
                question_and_options = self.non_response_question.text % (
                    self.household1.uid, self.household_head.surname) + non_response_option_page
                non_response_question = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

                with patch.object(USSDSurvey, "is_active", return_value=True):
                    response = self.reset_session()

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['YES'])
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

                response = self.respond("3")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['NON_RESPONSE_COMPLETION']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(3, MultiChoiceAnswer.objects.get(investigator=self.investigator, batch=self.batch,
                                                                   question=self.non_response_question,
                                                                   household=self.household1).answer.order)

                response = self.reset_session()

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['NO'])
                homepage = "Welcome %s to the survey.\n" \
                           "1: Register households\n" \
                           "2: Take survey\n" \
                           "3: Report non-response" % self.investigator.name
                response_string = "responseString=%s&action=request" % homepage
                self.assertEqual(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['TAKE_SURVEY'])

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s" \
                                 % (self.household1.uid, self.household_head.surname)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

                response = self.select_household("1")
                households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                expected_screen = "%s\n1: %s - (respondent)" % households_member_list
                response_string = "responseString=%s&action=request" % expected_screen
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("1")
                response_string = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("3")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(3, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_1,
                                                                 household=self.household1).answer)

                response = self.respond(USSD.ANSWER['NO'])
                response_string = "responseString=%s&action=end" % USSD.MESSAGES[
                    'SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS']
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_resume_from_non_response_to_register_household_to_non_response(self):
        self.batch.activate_non_response_for(self.kampala)

        self.household2.delete()
        self.household3.delete()
        self.household4.delete()

        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
        }

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                self.choose_menu_to_report_non_response()
                response = self.select_household("1")
                non_response_option_page = "\n1: House closed\n2: Household moved\n3: Refused to answer\n#: Next"
                question_and_options = self.non_response_question.text % (
                    self.household1.uid, self.household_head.surname) + non_response_option_page
                non_response_question = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

                with patch.object(USSDSurvey, "is_active", return_value=True):
                    response = self.reset_session()

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['YES'])
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

                response = self.respond("3")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['NON_RESPONSE_COMPLETION']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(3, MultiChoiceAnswer.objects.get(investigator=self.investigator, batch=self.batch,
                                                                   question=self.non_response_question,
                                                                   household=self.household1).answer.order)

                response = self.reset_session()

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['NO'])
                homepage = "Welcome %s to the survey.\n" \
                           "1: Register households\n" \
                           "2: Take survey\n" \
                           "3: Report non-response" % self.investigator.name
                homepage_response_string = "responseString=%s&action=request" % homepage
                self.assertEqual(urllib2.unquote(response.content), homepage_response_string)

                self.household2 = self.create_household(2)

                response = self.respond(USSD.ANSWER['REGISTER_HOUSEHOLD'])

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s\n2: HH-%s" \
                                 % (self.household1.uid, self.household_head.surname, self.household2.uid)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

                response = self.select_household("2")
                select_member_or_head = USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % self.household2.uid
                response_string = "responseString=%s&action=request" % select_member_or_head
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.respond('1')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                self.assertEqual(1, self.household2.household_member.count())
                member = self.household2.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, True)

                response = self.reset_session()
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['NO'])
                self.assertEqual(urllib2.unquote(response.content), homepage_response_string)

                response = self.choose_menu_to_report_non_response()

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s*\n2: HH-%s-%s" \
                                 % (self.household1.uid, self.household_head.surname,
                                    self.household2.uid, self.household2.get_head().surname)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

    def test_resume_from_register_to_non_response_without_reset_session(self):
        self.batch.activate_non_response_for(self.kampala)
        self.household2.delete()
        self.household3.delete()
        self.household4.delete()

        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age}

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                response = self.reset_session()
                homepage = "Welcome %s to the survey.\n" \
                           "1: Register households\n" \
                           "2: Take survey\n" \
                           "3: Report non-response" % self.investigator.name
                homepage_response_string = "responseString=%s&action=request" % homepage
                self.assertEqual(urllib2.unquote(response.content), homepage_response_string)

                self.household2 = self.create_household(2)

                response = self.respond(USSD.ANSWER['REGISTER_HOUSEHOLD'])

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s\n2: HH-%s" \
                                 % (self.household1.uid, self.household_head.surname, self.household2.uid)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

                response = self.select_household("2")
                select_member_or_head = USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % self.household2.uid
                response_string = "responseString=%s&action=request" % select_member_or_head
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.respond('1')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                self.assertEqual(1, self.household2.household_member.count())
                member = self.household2.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, True)

                response = self.respond(USSD.ANSWER['NO'])
                self.assertEqual(urllib2.unquote(response.content), homepage_response_string)

                response = self.choose_menu_to_report_non_response()

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s\n2: HH-%s-%s" \
                                 % (self.household1.uid, self.household_head.surname,
                                    self.household2.uid, self.household2.get_head().surname)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

                response = self.select_household("1")
                non_response_option_page = "\n1: House closed\n2: Household moved\n3: Refused to answer\n#: Next"
                question_and_options = self.non_response_question.text % (
                    self.household1.uid, self.household_head.surname) + non_response_option_page
                non_response_question = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

    def test_transition_from_take_survey_to_non_response(self):
        self.batch.activate_non_response_for(self.kampala)

        self.household3.delete()
        self.household4.delete()
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(USSDSurvey, "is_active", return_value=False):
                    response = self.reset_session()
                homepage = "Welcome %s to the survey.\n" \
                           "1: Register households\n" \
                           "2: Take survey\n" \
                           "3: Report non-response" % self.investigator.name
                response_string = "responseString=%s&action=request" % homepage
                self.assertEqual(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['TAKE_SURVEY'])
                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s\n2: HH-%s-%s" \
                % (self.household1.uid, self.household_head.surname, self.household2.uid, self.household_head2.surname)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

                response = self.select_household("1")
                households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], self.household_head.surname)
                expected_screen = "%s\n1: %s - (respondent)" % households_member_list
                response_string = "responseString=%s&action=request" % expected_screen
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.select_household_member("1")
                response_string = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("3")
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.assertEquals(3, NumericalAnswer.objects.get(investigator=self.investigator, question=self.question_1,
                                                                 household=self.household1).answer)

                with patch.object(USSDSurvey, "is_active", return_value=False):
                    response = self.reset_session()
                homepage = "Welcome %s to the survey.\n" \
                           "1: Register households\n" \
                           "2: Take survey\n" \
                           "3: Report non-response" % self.investigator.name
                response_string = "responseString=%s&action=request" % homepage
                self.assertEqual(urllib2.unquote(response.content), response_string)

                response = self.choose_menu_to_report_non_response()
                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s" \
                                % (self.household2.uid, self.household_head2.surname)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

                response = self.select_household("1")
                non_response_option_page = "\n1: House closed\n2: Household moved\n3: Refused to answer\n#: Next"
                question_and_options = self.non_response_question.text % (
                    self.household2.uid, self.household_head2.surname) + non_response_option_page
                non_response_question = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

    def test_resume_non_response_to_non_response(self):
        household_member_3_1 = self.create_household_member(name="bob 3 son", household=self.household3, head=False,
                                                            date_of_birth="1996-9-9")
        household_member_3_2 = self.create_household_member(name="bob 3 son 2", household=self.household3, head=False,
                                                            date_of_birth="1996-9-4")
        household_member_who_completed = self.create_household_member(name="bob 3 good son", household=self.household3,
                                                                      head=False, date_of_birth="1996-9-1")
        household_member_who_completed.batch_completed(self.batch)

        self.batch.activate_non_response_for(self.kampala)
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_report_non_response()
                self.select_household("3")
                self.select_household_member("2")
                self.respond("1")
                response = self.select_household_member("3")
                non_response_option_page = "\n1: Member Refused\n2: Reason"
                question_and_options = self.member_non_response_question.text % household_member_3_2.surname + non_response_option_page
                non_response_question = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

                with patch.object(USSDSurvey, "is_active", return_value=True):
                    response = self.reset_session()

                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['YES'])
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

                response = self.respond("2")
                households_member_list = (USSD.MESSAGES['MEMBERS_LIST'], self.household_head3.surname,
                                          household_member_3_1.surname, household_member_3_2.surname)
                expected_screen_page_1 = "%s\n1: %s - (respondent)\n2: %s*\n3: %s*" % households_member_list
                member_list_page_1 = "responseString=%s&action=request" % expected_screen_page_1
                self.assertEquals(urllib2.unquote(response.content), member_list_page_1)

    def test_transition_non_response_resume_register_household(self):
        self.batch.activate_non_response_for(self.kampala)

        self.household2.delete()
        self.household3.delete()
        self.household4.delete()

        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
        }

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                with patch.object(Investigator, "was_active_within", return_value=False):
                    self.reset_session()
                self.choose_menu_to_report_non_response()
                response = self.select_household("1")
                non_response_option_page = "\n1: House closed\n2: Household moved\n3: Refused to answer\n#: Next"
                question_and_options = self.non_response_question.text % (
                    self.household1.uid, self.household_head.surname) + non_response_option_page
                non_response_question = "responseString=%s&action=request" % question_and_options
                self.assertEquals(urllib2.unquote(response.content), non_response_question)

                response = self.reset_session()

                homepage = "Welcome %s to the survey.\n" \
                           "1: Register households\n" \
                           "2: Take survey\n" \
                           "3: Report non-response" % self.investigator.name
                homepage_response_string = "responseString=%s&action=request" % homepage
                self.assertEqual(urllib2.unquote(response.content), homepage_response_string)

                self.household2 = self.create_household(2)

                response = self.respond(USSD.ANSWER['REGISTER_HOUSEHOLD'])

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s\n2: HH-%s" \
                                 % (self.household1.uid, self.household_head.surname, self.household2.uid)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

                response = self.select_household("2")
                select_member_or_head = USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % self.household2.uid
                response_string = "responseString=%s&action=request" % select_member_or_head
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.respond('1')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                self.assertEqual(1, self.household2.household_member.count())
                member = self.household2.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, True)

                response = self.reset_session()
                response_string = "responseString=%s&action=request" % USSD.MESSAGES['RESUME_MESSAGE']
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(USSD.ANSWER['NO'])
                self.assertEqual(urllib2.unquote(response.content), homepage_response_string)

                response = self.choose_menu_to_report_non_response()

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s-%s\n2: HH-%s-%s" \
                                 % (self.household1.uid, self.household_head.surname,
                                    self.household2.uid, self.household2.get_head().surname)
                first_page_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_list)

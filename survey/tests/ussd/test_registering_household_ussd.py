from random import randint
import datetime
import urllib2
from django.http import HttpRequest

from django.test import Client
from mock import patch
from rapidsms.contrib.locations.models import Location

from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Investigator, Backend, Household, Question, HouseholdMemberGroup, HouseholdHead, QuestionModule, AnswerRule, QuestionOption, Survey, RandomHouseHoldSelection, Batch
from survey.tests.ussd.ussd_base_test import USSDBaseTest
from survey.ussd.ussd import USSD
from survey.ussd.ussd_register_household import USSDRegisterHousehold


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
        self.another_open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        self.open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)

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
        self.household5 = self.create_household(5)

    def test_set_is_selecting_member_for_register_household(self):
        with patch.object(Investigator, 'get_from_cache') as get_from_cache:
                USSDRegisterHousehold.REGISTRATION_DICT = {}
                exception = KeyError()
                get_from_cache.side_effect = exception
                ussd_register_household = USSDRegisterHousehold(self.investigator, FakeRequest())

        self.assertEqual({}, ussd_register_household.REGISTRATION_DICT)
        self.assertFalse(self.investigator.get_from_cache('is_selecting_member'))
        self.assertIsNone(ussd_register_household.is_head)

        with patch.object(USSD, 'get_from_session') as get_from_session:
            exception = KeyError()
            get_from_session.side_effect = exception
            ussd_register_household.set_can_retake_household()
            self.assertFalse(ussd_register_household.can_retake_household)

            ussd_register_household.set_has_chosen_retake()
            self.assertFalse(ussd_register_household.has_chosen_retake)

    def test_register_households_knows_household_from_cache_if_resuming(self):
        with patch.object(USSD, 'get_from_session', return_value=True):
            ussd_register_household = USSDRegisterHousehold(self.investigator, FakeRequest())
            ussd_register_household.household = None
            with patch.object(Investigator, 'get_from_cache', return_value=self.household1):
                ussd_register_household.register_households('1')

        self.assertEqual(ussd_register_household.household, self.household1)

    def test_process_registration_with_invalid_answer(self):
        module = QuestionModule.objects.create(name='Registration')
        registration_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)
        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=registration_group)

        ussd_register_household = USSDRegisterHousehold(self.investigator, FakeRequest())
        ussd_register_household.question = question_1

        self.assertEqual(question_1, ussd_register_household.process_registration_answer(''))

    def create_household(self, unique_id):
        return Household.objects.create(investigator=self.investigator, location=self.investigator.location,
                                        uid=unique_id, random_sample_number=unique_id, survey=self.open_survey)

    def test_should_show_list_of_households_with_uids_when_selected_option_to_register_household_and_pagination(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                response = self.register_household()
                household_list = USSD.MESSAGES[
                                     'HOUSEHOLD_LIST'] + "\n1: Household-%s\n2: Household-%s\n3: Household-%s\n4: Household-%s\n#: Next" % (
                                     self.household1.uid, self.household2.uid, self.household3.uid, self.household4.uid)

                first_page_HH_list = "responseString=%s&action=request" % (household_list)
                self.assertEquals(urllib2.unquote(response.content), first_page_HH_list)

                response = self.respond("#")

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n5: Household-%s\n*: Back" % (self.household5.uid)

                response_string = "responseString=%s&action=request" % (household_list)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("*")
                self.assertEquals(urllib2.unquote(response.content), first_page_HH_list)

    def test_should_show_invalid_selection_if_wrong_household_option_selected(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                response = self.register_household()
                household_list = USSD.MESSAGES[
                                     'HOUSEHOLD_LIST'] + "\n1: Household-%s\n2: Household-%s\n3: Household-%s\n4: Household-%s\n#: Next" % (
                                     self.household1.uid, self.household2.uid, self.household3.uid, self.household4.uid)

                first_page_HH_list = "responseString=%s&action=request" % (household_list)
                self.assertEquals(urllib2.unquote(response.content), first_page_HH_list)


                response = self.respond("70")
                household_list = "INVALID SELECTION: "+ household_list
                first_page_HH_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_HH_list)

    def test_should_show_list_of_households_when_another_survey_open_in_different_location(self):
        batch = Batch.objects.create(order=7, name="Batch name", survey=self.another_open_survey)
        batch.open_for_location(self.entebbe)

        batch_2 = Batch.objects.create(order=8, name="Another Batch", survey=self.open_survey)
        batch_2.open_for_location(self.kampala)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            self.reset_session()
            response = self.register_household()
            household_list = USSD.MESSAGES[
                                 'HOUSEHOLD_LIST'] + "\n1: Household-%s\n2: Household-%s\n3: Household-%s\n4: Household-%s\n#: Next" % (
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
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()

                response = self.select_household("2")

                ask_member_response_string = "responseString=%s&action=request" \
                                             % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % \
                                             self.household2.random_sample_number
                self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_should_ask_show_welcome_text_if_resuming_and_no_is_chosen(self):
        answers = {'name': 'dummy name',
                   'age': '10',
                   'gender': '1'
        }
        module = QuestionModule.objects.create(name='Registration')
        self.registration_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        Question.objects.create(module=module, text="Please Enter the age",
                                answer_type=Question.TEXT, order=2, group=self.registration_group)

        Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                answer_type=Question.NUMBER, order=3, group=self.registration_group)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()

                self.select_household("2")
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['gender'])

                self.reset_session()
                response = self.respond('2')

                homepage = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
                response_string = "responseString=%s&action=request" % homepage
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_should_render_first_registration_question_when_selected_member_for_registration(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)
        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)
        question_2 = Question.objects.create(module=module, text="Please Enter the age\n(enter 99 if not known)",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()
                self.select_household("2")
                response = self.respond('2')
                first_registration_question = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)

    def test_should_render_next_registration_question_when_answered_one(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)
        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)
        question_2 = Question.objects.create(module=module, text="Please Enter the age\n(enter 99 if not known)",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()
                self.select_household("2")
                self.respond('2')
                response = self.respond('Dummy name')
                next_registration_question = "responseString=%s&action=request" % question_2.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

    def test_should_render_third_registration_question_when_answered_two(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age\n(enter 99 if not known)",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()
                self.select_household("2")
                self.respond('2')
                self.respond('Dummy name')
                response = self.respond("32")
                next_registration_question = "responseString=%s&action=request" % question_3.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

    def test_should_save_member_if_all_questions_answered(self):
        answers = {'name': 'dummy name',
                   'age': '10',
                   'gender': '2'
        }
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age\n(enter 99 if not known)",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender:\n1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household.household_member.count())
                member = selected_household.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, False)

    def test_should_render_date_of_birth_registration_question_if_age_question_answer_is_empty_and_saves_member_when_all_questions_answered(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age\n(enter 99 if not known)",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        month = Question.objects.create(module=module, text="Please Enter the month of birth",
                                             answer_type=Question.MULTICHOICE, group=self.registration_group,
                                        subquestion=True, parent=question_2)
        QuestionOption.objects.create(question=month, text="January", order=1)
        QuestionOption.objects.create(question=month, text="February", order=2)
        QuestionOption.objects.create(question=month, text="March", order=3)
        QuestionOption.objects.create(question=month, text="April", order=4)
        QuestionOption.objects.create(question=month, text="May", order=5)
        QuestionOption.objects.create(question=month, text="June", order=6)
        QuestionOption.objects.create(question=month, text="July", order=7)
        QuestionOption.objects.create(question=month, text="August", order=8)
        QuestionOption.objects.create(question=month, text="September", order=9)
        QuestionOption.objects.create(question=month, text="October", order=10)
        QuestionOption.objects.create(question=month, text="November", order=11)
        QuestionOption.objects.create(question=month, text="December", order=12)

        year = Question.objects.create(module=module, text="Please Enter the year of birth",
                                             answer_type=Question.NUMBER, group=self.registration_group,
                                        subquestion=True, parent=question_2)

        AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                  condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=99,
                                  next_question=month)

        AnswerRule.objects.create(question=month, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                  condition=AnswerRule.CONDITIONS['BETWEEN'], validate_with_min_value=1,
                                  validate_with_max_value=12, next_question=year)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        answers = {
            'name': 'dummy name',
           'age': '99',
           'month':'4',
           'year':'2001',
           'gender': '2',
        }
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                response = self.respond(answers['age'])
                MONTHS_OPTION_PAGE_1="\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (month.text + MONTHS_OPTION_PAGE_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)
                response = self.respond(answers['month'])
                next_registration_question = "responseString=%s&action=request" % year.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)
                response = self.respond(answers['year'])
                next_registration_question = "responseString=%s&action=request" % question_3.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)
                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household.household_member.count())
                member = selected_household.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, False)
                self.assertEqual(member.date_of_birth, datetime.date(int(answers['year']), int(answers['month']), 1))

    def test_invalid_month_of_birth_renders_invalid_selection_and_a_subsequent_valid_answer_render_year_of_birth(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age\n(enter 99 if not known)",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        month = Question.objects.create(module=module, text="Please Enter the month of birth",
                                             answer_type=Question.MULTICHOICE, group=self.registration_group,
                                        subquestion=True, parent=question_2)
        QuestionOption.objects.create(question=month, text="January", order=1)
        QuestionOption.objects.create(question=month, text="February", order=2)
        QuestionOption.objects.create(question=month, text="March", order=3)
        QuestionOption.objects.create(question=month, text="April", order=4)
        QuestionOption.objects.create(question=month, text="May", order=5)
        QuestionOption.objects.create(question=month, text="June", order=6)
        QuestionOption.objects.create(question=month, text="July", order=7)
        QuestionOption.objects.create(question=month, text="August", order=8)
        QuestionOption.objects.create(question=month, text="September", order=9)
        QuestionOption.objects.create(question=month, text="October", order=10)
        QuestionOption.objects.create(question=month, text="November", order=11)
        QuestionOption.objects.create(question=month, text="December", order=12)

        year = Question.objects.create(module=module, text="Please Enter the year of birth",
                                             answer_type=Question.NUMBER, group=self.registration_group,
                                        subquestion=True, parent=question_2)

        AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                  condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=99,
                                  next_question=month)

        AnswerRule.objects.create(question=month, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                  condition=AnswerRule.CONDITIONS['BETWEEN'], validate_with_min_value=1,
                                  validate_with_max_value=12, next_question=year)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        invalid_month_of_birth = '40'
        answers = {
            'name': 'dummy name',
           'age': '99',
           'month':invalid_month_of_birth,
           'year':'2001',
           'gender': '2',
        }

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                response = self.respond(answers['age'])
                MONTHS_OPTION_PAGE_1="\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (month.text + MONTHS_OPTION_PAGE_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(answers['month'])
                next_registration_question = "responseString=%s&action=request" % ("INVALID ANSWER: " + month.text + MONTHS_OPTION_PAGE_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                another_invalid_month ='bla&bli**blo#@!'
                response = self.respond(another_invalid_month)
                next_registration_question = "responseString=%s&action=request" % ("INVALID ANSWER: " + month.text + MONTHS_OPTION_PAGE_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                valid_month = '2'
                response = self.respond(valid_month)
                next_registration_question = "responseString=%s&action=request" % year.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(answers['year'])
                next_registration_question = "responseString=%s&action=request" % question_3.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)


                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household.household_member.count())
                member = selected_household.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, False)
                self.assertEqual(member.date_of_birth, datetime.date(int(answers['year']), int(valid_month), 1))

    def test_month_of_birth_paginations_and_invalid_month_integration(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age\n(enter 99 if not known)",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        month = Question.objects.create(module=module, text="Please Enter the month of birth",
                                             answer_type=Question.MULTICHOICE, group=self.registration_group,
                                        subquestion=True, parent=question_2)
        QuestionOption.objects.create(question=month, text="January", order=1)
        QuestionOption.objects.create(question=month, text="February", order=2)
        QuestionOption.objects.create(question=month, text="March", order=3)
        QuestionOption.objects.create(question=month, text="April", order=4)
        QuestionOption.objects.create(question=month, text="May", order=5)
        QuestionOption.objects.create(question=month, text="June", order=6)
        QuestionOption.objects.create(question=month, text="July", order=7)
        QuestionOption.objects.create(question=month, text="August", order=8)
        QuestionOption.objects.create(question=month, text="September", order=9)
        QuestionOption.objects.create(question=month, text="October", order=10)
        QuestionOption.objects.create(question=month, text="November", order=11)
        QuestionOption.objects.create(question=month, text="December", order=12)

        year = Question.objects.create(module=module, text="Please Enter the year of birth",
                                             answer_type=Question.NUMBER, group=self.registration_group,
                                        subquestion=True, parent=question_2)

        AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                  condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=99,
                                  next_question=month)

        AnswerRule.objects.create(question=month, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                  condition=AnswerRule.CONDITIONS['BETWEEN'], validate_with_min_value=1,
                                  validate_with_max_value=12, next_question=year)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        answers = {
            'name': 'dummy name',
           'age': '99',
           'month':'4',
           'year':'2001',
           'gender': '2',
        }

        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                response = self.respond(answers['age'])
                MONTHS_OPTION_PAGE_1="\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (month.text + MONTHS_OPTION_PAGE_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                invalid_month ='bla&bli**blo#@!'
                response = self.respond(invalid_month)
                next_registration_question = "responseString=%s&action=request" % ("INVALID ANSWER: " + month.text + MONTHS_OPTION_PAGE_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond('#')
                MONTHS_OPTION_PAGE_2="\n4: April\n5: May\n6: June\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (month.text + MONTHS_OPTION_PAGE_2)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(invalid_month)
                next_registration_question = "responseString=%s&action=request" % ("INVALID ANSWER: " + month.text + MONTHS_OPTION_PAGE_2)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond('#')
                MONTHS_OPTION_PAGE_3="\n7: July\n8: August\n9: September\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (month.text + MONTHS_OPTION_PAGE_3)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(invalid_month)
                MONTHS_OPTION_PAGE_3="\n7: July\n8: August\n9: September\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % ("INVALID ANSWER: " + month.text + MONTHS_OPTION_PAGE_3)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond('#')
                MONTHS_OPTION_PAGE_4="\n10: October\n11: November\n12: December\n*: Back"
                next_registration_question = "responseString=%s&action=request" % (month.text + MONTHS_OPTION_PAGE_4)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond('*')
                MONTHS_OPTION_PAGE_3="\n7: July\n8: August\n9: September\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (month.text + MONTHS_OPTION_PAGE_3)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(invalid_month)
                MONTHS_OPTION_PAGE_3="\n7: July\n8: August\n9: September\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % ("INVALID ANSWER: " + month.text + MONTHS_OPTION_PAGE_3)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                valid_month = '8'
                response = self.respond(valid_month)
                next_registration_question = "responseString=%s&action=request" % year.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(answers['year'])
                next_registration_question = "responseString=%s&action=request" % question_3.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)


                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household.household_member.count())
                member = selected_household.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, False)
                self.assertEqual(member.date_of_birth, datetime.date(int(answers['year']), int(valid_month), 1))

    def test_should_save_household_head_object(self):
        answers = {'name': 'dummy name',
                   'age': '10',
                   'gender': '1'
        }
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age",
                                             answer_type=Question.TEXT, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('1')
                self.respond(answers['name'])
                self.respond(answers['age'])
                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                self.assertIsNotNone(selected_household.get_head())
                head = selected_household.get_head()
                self.assertEqual(head.surname, answers['name'])
                self.assertTrue(head.male)

    def test_should_go_back_to_member_or_head_screen_when_a_member_registered(self):
        answers = {'name': 'dummy name',
                   'age': '10',
                   'gender': '1'
        }
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                HouseholdHead.objects.all().delete()
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['gender'])

                response = self.respond('1')
                ask_member_response_string = "responseString=%s&action=request" % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] \
                                             % self.household2.random_sample_number
                self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_should_go_back_to_welcome_screen_if_responds_no_after_registering_a_member(self):
        answers = {'name': 'dummy name',
                   'age': '10',
                   'gender': '1'
        }
        self.registration_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)
        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age",
                                             answer_type=Question.TEXT, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('1')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['gender'])

                response = self.respond('2')
                welcome_text = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
                ask_member_response_string = "responseString=%s&action=request" % welcome_text
                self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_should_ask_member_question_after_registering_head_if_investigator_responds_with_yes_to_register_other_members(
            self):
        answers = {'name': 'dummy name',
                   'age': '10',
                   'gender': '1'
        }
        self.registration_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)
        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        Question.objects.create(module=module, text="Please Enter the age",
                                answer_type=Question.TEXT, order=2, group=self.registration_group)

        Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                answer_type=Question.NUMBER, order=3, group=self.registration_group)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('1')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['gender'])

                response = self.respond('1')
                first_registration_question = "responseString=%s%s&action=request" % (
                    USSD.MESSAGES['HEAD_REGISTERED'], question_1.text)
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)

    def test_complete_registration_flow_with_valid_age(self):
        answers = {'name': 'dummy name',
                   'age': '10',
                   'gender': '1'
        }
        module = QuestionModule.objects.create(name='Registration')
        self.registration_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        Question.objects.create(module=module, text="Please Enter the age",
                                answer_type=Question.TEXT, order=2, group=self.registration_group)

        Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                answer_type=Question.NUMBER, order=3, group=self.registration_group)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['gender'])

                response = self.respond('1')
                select_head_or_member = "responseString=%s&action=request" % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % \
                                        self.household2.random_sample_number
                self.assertEquals(urllib2.unquote(response.content), select_head_or_member)
                response = self.respond('1')
                first_registration_question = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['gender'])

                response = self.respond('1')
                first_registration_question = "responseString=%s%s&action=request" % (
                    USSD.MESSAGES['HEAD_REGISTERED'], question_1.text)
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['gender'])

                response = self.respond('2')
                welcome_text = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
                ask_member_response_string = "responseString=%s&action=request" % welcome_text
                self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_complete_registration_flow_with_invalid_age_and_months_and_year_of_birth_asked(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                                          order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age\n(enter 99 if not known)",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        month = Question.objects.create(module=module, text="Please Enter the month of birth",
                                             answer_type=Question.MULTICHOICE, group=self.registration_group,
                                        subquestion=True, parent=question_2)
        QuestionOption.objects.create(question=month, text="January", order=1)
        QuestionOption.objects.create(question=month, text="February", order=2)
        QuestionOption.objects.create(question=month, text="March", order=3)
        QuestionOption.objects.create(question=month, text="April", order=4)
        QuestionOption.objects.create(question=month, text="May", order=5)
        QuestionOption.objects.create(question=month, text="June", order=6)
        QuestionOption.objects.create(question=month, text="July", order=7)
        QuestionOption.objects.create(question=month, text="August", order=8)
        QuestionOption.objects.create(question=month, text="September", order=9)
        QuestionOption.objects.create(question=month, text="October", order=10)
        QuestionOption.objects.create(question=month, text="November", order=11)
        QuestionOption.objects.create(question=month, text="December", order=12)

        year = Question.objects.create(module=module, text="Please Enter the year of birth",
                                             answer_type=Question.NUMBER, group=self.registration_group,
                                        subquestion=True, parent=question_2)

        AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                  condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=99,
                                  next_question=month)

        AnswerRule.objects.create(question=month, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                  condition=AnswerRule.CONDITIONS['BETWEEN'], validate_with_min_value=1,
                                  validate_with_max_value=12, next_question=year)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        answers = {
            'name': 'dummy name',
           'age': '99',
           'month':'3',
           'year':'2001',
           'gender': '1',
        }
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                self.respond(answers['gender'])

                response = self.respond('1')
                select_head_or_member = "responseString=%s&action=request" % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % \
                                        self.household2.random_sample_number

                self.assertEquals(urllib2.unquote(response.content), select_head_or_member)
                response = self.respond('1')
                first_registration_question = "responseString=%s&action=request" % question_1.text
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                self.respond(answers['gender'])

                response = self.respond('1')
                first_registration_question = "responseString=%s%s&action=request" % (
                    USSD.MESSAGES['HEAD_REGISTERED'], question_1.text)
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                self.respond(answers['gender'])

                response = self.respond('2')
                welcome_text = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
                ask_member_response_string = "responseString=%s&action=request" % welcome_text
                self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_should_not_give_member_select_screen_if_head_already_registered(self):
        self.registration_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)
        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        Question.objects.create(module=module, text="Please Enter the age",
                                answer_type=Question.TEXT, order=2, group=self.registration_group)

        Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                answer_type=Question.NUMBER, order=3, group=self.registration_group)
        selected_household_id = '2'
        household = Household.objects.get(uid=selected_household_id)
        head = HouseholdHead.objects.create(household=household, surname="head_registered",
                                            date_of_birth=datetime.datetime(1980, 02, 02), male=False)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=[1]):
                self.reset_session()
                self.register_household()
                response = self.select_household(selected_household_id)

                first_registration_question = "responseString=%s%s&action=request" % (
                    USSD.MESSAGES['HEAD_REGISTERED'], question_1.text)
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)

class FakeRequest(HttpRequest):
    def dict(self):
        obj = self.__dict__
        obj['transactionId'] = '1234567890'
        obj['response'] = 'false'
        return obj
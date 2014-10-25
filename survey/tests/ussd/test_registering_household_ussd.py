from calendar import monthrange
from random import randint
import datetime
import urllib2

from django.test import Client
from mock import patch, MagicMock
from rapidsms.contrib.locations.models import Location

from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Investigator, Backend, Household, Question, HouseholdMemberGroup, HouseholdHead, QuestionModule, QuestionOption, Survey, RandomHouseHoldSelection, Batch, UnknownDOBAttribute, HouseholdMember, EnumerationArea
from survey.tests.ussd.ussd_base_test import USSDBaseTest, FakeRequest
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
        self.another_open_survey = Survey.objects.create(name="open survey", description="open survey",
                                                         has_sampling=True)
        self.open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)

        self.kampala = Location.objects.create(name="Kampala")
        self.entebbe = Location.objects.create(name="Entebbe")

        self.ea = EnumerationArea.objects.create(name="EA2", survey=self.open_survey)
        self.ea.locations.add(self.kampala)

        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number=self.ussd_params['msisdn'].replace(
                                                            COUNTRY_PHONE_CODE, '', 1), ea=self.ea,
                                                        backend=self.backend)

        self.household1 = self.create_household(1)
        self.household2 = self.create_household(2)
        self.household3 = self.create_household(3)
        self.household4 = self.create_household(4)
        self.household5 = self.create_household(5)

        self.registration_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP",
                                                                      order=0)
        module = QuestionModule.objects.create(name='Registration')
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
        ussd_register_household = USSDRegisterHousehold(self.investigator, FakeRequest())
        ussd_register_household.question = self.question_1
        self.assertEqual(self.question_1, ussd_register_household.process_registration_answer(''))

    def create_household(self, unique_id):
        return Household.objects.create(investigator=self.investigator, ea=self.investigator.ea,
                                        uid=unique_id, random_sample_number=unique_id, survey=self.open_survey)

    def test_should_show_list_of_households_with_uids_when_selected_option_to_register_household_and_pagination(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                response = self.choose_menu_to_register_household()
                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n1: HH-%s" \
                                                                   "\n2: HH-%s" \
                                                                   "\n3: HH-%s" \
                                                                   "\n4: HH-%s" \
                                                                   "\n#: Next" % (
                                     self.household1.uid, self.household2.uid, self.household3.uid, self.household4.uid)

                first_page_hh_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_hh_list)

                response = self.respond("#")

                household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n5: HH-%s\n*: Back" % self.household5.uid

                response_string = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond("*")
                self.assertEquals(urllib2.unquote(response.content), first_page_hh_list)

    def test_should_show_invalid_selection_if_wrong_household_option_selected(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                response = self.choose_menu_to_register_household()
                household_list = USSD.MESSAGES[
                                     'HOUSEHOLD_LIST'] + "\n1: HH-%s\n2: HH-%s\n3: HH-%s\n4: HH-%s\n#: Next" % (
                                     self.household1.uid, self.household2.uid, self.household3.uid, self.household4.uid)

                first_page_hh_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_hh_list)

                response = self.respond("70")
                household_list = "INVALID SELECTION: " + household_list
                first_page_hh_list = "responseString=%s&action=request" % household_list
                self.assertEquals(urllib2.unquote(response.content), first_page_hh_list)

    def test_should_show_list_of_households_when_another_survey_open_in_different_location(self):
        batch = Batch.objects.create(order=7, name="Batch name", survey=self.another_open_survey)
        batch.open_for_location(self.entebbe)

        batch_2 = Batch.objects.create(order=8, name="Another Batch", survey=self.open_survey)
        batch_2.open_for_location(self.kampala)

        mock_filter = MagicMock()
        mock_filter.exists.return_value = True
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
            self.reset_session()
            response = self.choose_menu_to_register_household()
            household_list = USSD.MESSAGES[
                                 'HOUSEHOLD_LIST'] + "\n1: HH-%s\n2: HH-%s\n3: HH-%s\n4: HH-%s\n#: Next" % (
                                 self.household1.uid, self.household2.uid, self.household3.uid, self.household4.uid)

            first_page_hh_list = "responseString=%s&action=request" % household_list
            self.assertEquals(urllib2.unquote(response.content), first_page_hh_list)

            response = self.respond("#")

            household_list = USSD.MESSAGES['HOUSEHOLD_LIST'] + "\n5: HH-%s\n*: Back" % self.household5.uid

            response_string = "responseString=%s&action=request" % household_list
            self.assertEquals(urllib2.unquote(response.content), response_string)

            response = self.respond("*")
            self.assertEquals(urllib2.unquote(response.content), first_page_hh_list)

    def test_should_ask_for_head_or_member_after_selecting_household(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()

                response = self.select_household("2")

                ask_member_response_string = "responseString=%s&action=request" \
                                             % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % \
                                             self.household2.random_sample_number
                self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_should_ask_show_welcome_text_if_resuming_and_no_is_chosen(self):
        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
        }

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()

                self.select_household("2")
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                self.respond(answers['gender'])

                self.reset_session()
                response = self.respond('2')

                homepage = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
                response_string = "responseString=%s&action=request" % homepage
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_should_render_first_registration_question_when_selected_member_for_registration(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household("2")
                response = self.respond('2')
                first_registration_question = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)

    def test_should_render_next_registration_question_when_answered_one(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household("2")
                self.respond('2')
                response = self.respond('Dummy name')
                next_registration_question = "responseString=%s&action=request" % self.age_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

    def test_should_render_third_registration_question_when_answered_two(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household("2")
                self.respond('2')
                self.respond('Dummy name')
                response = self.respond("32")
                months_options_page_1 = "\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_options_page_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

    def test_should_ensure_that_age_is_not_empty(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household("2")
                self.respond('2')
                self.respond('Dummy name')
                response = self.respond(" ")
                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + self.age_question.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)
                response = self.respond(" ")
                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + self.age_question.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_should_show_month_and_year_question_given_a_valid_age_was_entered(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household("2")
                self.respond('2')
                self.respond('Dummy name')
                response = self.respond("34")
                months_option_page = "\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond("4")
                next_registration_question = "responseString=%s&action=request" % self.year_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

    def test_re_answer_age_questions_if_age_inferred_from_year_and_months_entered_does_not_match_age_earlier_given(
            self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household("2")
                self.respond('2')
                self.respond('Dummy name')
                self.respond("34")
                self.respond("4")
                response = self.respond("1989")
                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + self.age_question.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_re_answer_all_age_questions_given_age_given_does_not_match_inferred_age_from_date_of_birth(self):
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household("2")
                self.respond('2')
                self.respond('Dummy name')
                age = "34"
                self.respond(age)
                self.respond("4")
                response = self.respond("1989")
                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + self.age_question.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)
                response = self.respond("34")
                months_options = "\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_options)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)
                response = self.respond("4")
                response_string = "responseString=%s&action=request" % self.year_question.text
                self.assertEquals(urllib2.unquote(response.content), response_string)
                correct_year_of_birth = datetime.date.today().year - int(age)
                response = self.respond(correct_year_of_birth)
                response_string = "responseString=%s&action=request" % self.gender_question.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

    def test_should_save_member_if_all_questions_answered(self):
        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
        }

        mock_filter = MagicMock()
        mock_filter.exists.return_value = True
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household.household_member.count())
                member = selected_household.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, True)

    def test_should_render_date_of_birth_questions_after_age_question_and_save_member_when_all_questions_answered(self):
        answers = {
            'name': 'dummy name',
            'age': '0',
            'month': '4',
            'year': '2001',
            'gender': '2',
        }
        mock_filter = MagicMock()
        mock_filter.exists.return_value = True
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                response = self.respond(answers['age'])
                months_option_page_1 = "\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)
                response = self.respond(answers['month'])
                next_registration_question = "responseString=%s&action=request" % self.year_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)
                response = self.respond(answers['year'])
                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + self.age_question.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)
                response = self.respond(answers['age'])
                months_option_page_1 = "\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page_1)
                response = self.respond(answers['month'])
                next_registration_question = "responseString=%s&action=request" % self.year_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)
                response = self.respond(datetime.datetime.now().year)
                next_registration_question = "responseString=%s&action=request" % self.gender_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)
                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household.household_member.count())
                member = selected_household.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, False)
                today = datetime.date.today()
                self.assertEqual(member.date_of_birth, today.replace(month=int(answers['month'])))

    def test_invalid_month_of_birth_renders_invalid_selection_and_a_subsequent_valid_answer_render_year_of_birth(self):
        invalid_month_of_birth = '40'
        _some_age = '0'
        answers = {
            'name': 'dummy name',
            'age': _some_age,
            'month': invalid_month_of_birth,
            'year': datetime.datetime.today().year - int(_some_age),
            'gender': '2',
        }

        mock_filter = MagicMock()
        mock_filter.exists.return_value = True
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                response = self.respond(answers['age'])
                months_option_page_1 = "\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(answers['month'])
                next_registration_question = "responseString=%s&action=request" % (
                    "INVALID ANSWER: " + self.month_question.text + months_option_page_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                another_invalid_month = 'bla&bli**blo#@!'
                response = self.respond(another_invalid_month)
                next_registration_question = "responseString=%s&action=request" % (
                    "INVALID ANSWER: " + self.month_question.text + months_option_page_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)
                valid_month = '2'
                response = self.respond(valid_month)
                next_registration_question = "responseString=%s&action=request" % self.year_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(answers['year'])
                next_registration_question = "responseString=%s&action=request" % self.gender_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                today = datetime.date.today()
                day = min(today.day, monthrange(answers['year'], int(valid_month))[1])
                self.assertEqual(1, selected_household.household_member.count())
                member = selected_household.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, False)
                self.assertEqual(member.date_of_birth,
                                 datetime.date(year=int(answers['year']), month=int(valid_month), day=day))

    def test_month_of_birth_paginations_and_invalid_month_integration(self):
        _some_age = '0'
        answers = {
            'name': 'dummy name',
            'age': _some_age,
            'month': '4',
            'year': datetime.datetime.today().year - int(_some_age),
            'gender': '2',
        }

        mock_filter = MagicMock()
        mock_filter.exists.return_value = True
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                response = self.respond(answers['age'])
                months_option_page_1 = "\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                invalid_month = '44'
                response = self.respond(invalid_month)
                next_registration_question = "responseString=%s&action=request" % (
                    "INVALID ANSWER: " + self.month_question.text + months_option_page_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond('#')
                months_option_page_2 = "\n4: April\n5: May\n6: June\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page_2)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                invalid_month = 'bla&bli**blo#@!'
                response = self.respond(invalid_month)
                next_registration_question = "responseString=%s&action=request" % (
                    "INVALID ANSWER: " + self.month_question.text + months_option_page_2)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond('#')
                months_option_page_3 = "\n7: July\n8: August\n9: September\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page_3)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                invalid_month = '-3'
                response = self.respond(invalid_month)
                months_option_page_3 = "\n7: July\n8: August\n9: September\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    "INVALID ANSWER: " + self.month_question.text + months_option_page_3)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond('#')
                months_option_page_4 = "\n10: October\n11: November\n12: December\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page_4)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond('#')
                months_option_page_5 = "\n99: DONT KNOW\n*: Back"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page_5)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                self.respond('*')
                response = self.respond('*')
                months_option_page_3 = "\n7: July\n8: August\n9: September\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    self.month_question.text + months_option_page_3)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                invalid_month = '200'
                response = self.respond(invalid_month)
                months_option_page_3 = "\n7: July\n8: August\n9: September\n*: Back\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    "INVALID ANSWER: " + self.month_question.text + months_option_page_3)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                valid_month = '8'
                response = self.respond(valid_month)
                next_registration_question = "responseString=%s&action=request" % self.year_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(answers['year'])
                next_registration_question = "responseString=%s&action=request" % self.gender_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household.household_member.count())
                member = selected_household.household_member.all()[0]
                self.assertEqual(member.surname, answers['name'])
                self.assertEqual(member.male, False)
                today = datetime.date.today()
                self.assertEqual(member.date_of_birth, today.replace(year=int(answers['year']), month=int(valid_month)))

    def test_should_save_household_head_object(self):
        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
        }

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('1')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                response = self.respond(answers['gender'])
                end_registration_text = "responseString=%s&action=request" % USSD.MESSAGES['END_REGISTRATION']
                self.assertEquals(urllib2.unquote(response.content), end_registration_text)

                selected_household = Household.objects.get(uid=selected_household_id)
                self.assertIsNotNone(selected_household.get_head())
                head = selected_household.get_head()
                self.assertEqual(head.surname, answers['name'])
                self.assertTrue(head.male)

    def test_should_go_back_to_member_or_head_screen_when_a_member_registered(self):
        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
        }
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                HouseholdHead.objects.all().delete()
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                self.respond(answers['gender'])

                response = self.respond('1')
                ask_member_response_string = "responseString=%s&action=request" % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] \
                                             % self.household2.random_sample_number
                self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_should_go_back_to_welcome_screen_if_responds_no_after_registering_a_member(self):
        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
        }
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('1')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                self.respond(answers['gender'])

                response = self.respond('2')
                welcome_text = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
                ask_member_response_string = "responseString=%s&action=request" % welcome_text
                self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_should_ask_member_question_after_registering_head_if_investigator_responds_with_yes_to_register_other_members(
            self):
        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
        }

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('1')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                self.respond(answers['gender'])

                response = self.respond('1')
                first_registration_question = "responseString=%s%s&action=request" % (
                    USSD.MESSAGES['HEAD_REGISTERED'], self.question_1.text)
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)

    def test_day_of_birth_should_be_adjusted_to_last_day_of_month_if_it_exceeds_the_number_of_days_in_the_given_month(self):
        some_age = 10
        year = datetime.datetime.now().year - some_age
        import calendar
        if calendar.isleap(year):
            year = year + 1
            some_age = some_age -1

        feb = '2'
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': feb,
                   'year': datetime.datetime.now().year - some_age}

        day_not_existing_in_feb = 29
        not_feb = 11
        date_this_year_with_day_not_existing_in_feb = datetime.date.today().replace(month=not_feb, day=day_not_existing_in_feb)
        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                with self.mock_date_today(date_this_year_with_day_not_existing_in_feb):
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
                    member = HouseholdMember.objects.filter(surname=answers['name'])
                    self.assertEqual(1, len(member))
                    self.assertEqual(28, member[0].date_of_birth.day)

    def test_complete_registration_flow_with_valid_age(self):
        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age}

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
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

                response = self.respond('1')
                select_head_or_member = "responseString=%s&action=request" % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % \
                                        self.household2.random_sample_number
                self.assertEquals(urllib2.unquote(response.content), select_head_or_member)
                response = self.respond('1')
                first_registration_question = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(answers['year'])
                self.respond(answers['gender'])

                response = self.respond('1')
                first_registration_question = "responseString=%s%s&action=request" % (
                    USSD.MESSAGES['HEAD_REGISTERED'], self.question_1.text)
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

    def test_complete_registration_flow_with_invalid_age_and_months_and_year_of_birth_asked(self):
        answers = {
            'name': 'dummy name',
            'age': '0',
            'month': '3',
            'year': '2001',
            'gender': '1',
        }
        mock_filter = MagicMock()
        mock_filter.exists.return_value = True
        with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
            with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                response = self.respond(answers['year'])

                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + self.age_question.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.respond(answers['age'])
                self.respond(answers['month'])
                response = self.respond(answers['year'])

                response_string = "responseString=%s&action=request" % ("INVALID ANSWER: " + self.age_question.text)
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.respond(answers['age'])
                self.respond(answers['month'])

                correct_year = datetime.datetime.now().year - int(answers['age'])

                response = self.respond(correct_year)
                response_string = "responseString=%s&action=request" % self.gender_question.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                self.respond(answers['gender'])
                response = self.respond('1')
                select_head_or_member = "responseString=%s&action=request" % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER'] % \
                                        self.household2.random_sample_number

                self.assertEquals(urllib2.unquote(response.content), select_head_or_member)

                response = self.respond('1')
                first_registration_question = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(correct_year)
                self.respond(answers['gender'])

                response = self.respond('1')
                first_registration_question = "responseString=%s%s&action=request" % (
                    USSD.MESSAGES['HEAD_REGISTERED'], self.question_1.text)
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)
                self.respond(answers['name'])
                self.respond(answers['age'])
                self.respond(answers['month'])
                self.respond(correct_year)
                self.respond(answers['gender'])

                response = self.respond('2')
                welcome_text = USSD.MESSAGES['WELCOME_TEXT'] % self.investigator.name
                ask_member_response_string = "responseString=%s&action=request" % welcome_text
                self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_should_not_give_member_select_screen_if_head_already_registered(self):
        selected_household_id = '2'
        household = Household.objects.get(uid=selected_household_id)
        head = HouseholdHead.objects.create(household=household, surname="head_registered",
                                            date_of_birth=datetime.datetime(1980, 02, 02), male=False)

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                response = self.select_household(selected_household_id)

                first_registration_question = "responseString=%s%s&action=request" % (
                    USSD.MESSAGES['HEAD_REGISTERED'], self.question_1.text)
                self.assertEquals(urllib2.unquote(response.content), first_registration_question)

    def test_renders_next_question_when_99_is_entered_for_months_and_year_of_birth_and_saves_age_and_unknown_dob_attributes(
            self):
        dont_know = '99'

        answers = {
            'name': 'dummy name',
            'age': '59',
            'month': dont_know,
            'year': dont_know,
            'gender': '1',
        }
        selected_household_id = '2'

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                response = self.respond(answers['month'])
                response_string = "responseString=%s&action=request" % self.year_question.text
                self.assertEquals(urllib2.unquote(response.content), response_string)
                response = self.respond(answers['year'])
                response_string = "responseString=%s&action=request" % self.gender_question.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(answers['gender'])

                selected_household_uid = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household_uid.household_member.count())
                saved_member = selected_household_uid.household_member.all()[0]
                self.assertEqual(saved_member.surname, answers['name'])
                self.assertEqual(saved_member.male, True)
                today = datetime.date.today()
                self.assertEqual(saved_member.date_of_birth, today.replace(year=today.year - int(answers['age'])))
                unknown_attr = UnknownDOBAttribute.objects.filter(household_member=saved_member)
                self.assertEqual(2, unknown_attr.count())
                types = unknown_attr.values_list('type', flat=True)
                self.assertIn('MONTH', types)
                self.assertIn('YEAR', types)

    def test_renders_next_question_when_only_year_is_99(self):
        dont_know = '99'

        answers = {
            'name': 'dummy name',
            'age': '59',
            'month': '3',
            'year': dont_know,
            'gender': '1',
        }
        selected_household_id = '2'

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                response = self.respond(answers['month'])
                response_string = "responseString=%s&action=request" % self.year_question.text
                self.assertEquals(urllib2.unquote(response.content), response_string)
                response = self.respond(answers['year'])
                response_string = "responseString=%s&action=request" % self.gender_question.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(answers['gender'])

                selected_household_uid = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household_uid.household_member.count())
                saved_member = selected_household_uid.household_member.all()[0]
                self.assertEqual(saved_member.surname, answers['name'])
                self.assertEqual(saved_member.male, True)
                today = datetime.date.today()
                self.assertEqual(saved_member.date_of_birth,
                                 today.replace(year=today.year - int(answers['age']), month=int(answers['month'])))

                unknown_attr = UnknownDOBAttribute.objects.filter(household_member=saved_member)
                self.assertEqual(1, unknown_attr.count())
                self.assertEqual('YEAR', unknown_attr[0].type)

    def test_renders_next_question_when_only_month_is_99(self):
        dont_know = '99'

        age = '59'
        answers = {
            'name': 'dummy name',
            'age': age,
            'month': dont_know,
            'year': datetime.datetime.today().year - int(age),
            'gender': '1',
        }
        selected_household_id = '2'

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                response = self.respond(answers['month'])
                response_string = "responseString=%s&action=request" % self.year_question.text
                self.assertEquals(urllib2.unquote(response.content), response_string)
                response = self.respond(answers['year'])
                response_string = "responseString=%s&action=request" % self.gender_question.text
                self.assertEquals(urllib2.unquote(response.content), response_string)

                response = self.respond(answers['gender'])

                selected_household_uid = Household.objects.get(uid=selected_household_id)
                self.assertEqual(1, selected_household_uid.household_member.count())
                saved_member = selected_household_uid.household_member.all()[0]
                self.assertEqual(saved_member.surname, answers['name'])
                self.assertEqual(saved_member.male, True)
                today = datetime.date.today()
                self.assertEqual(saved_member.date_of_birth,
                                 today.replace(year=today.year - int(answers['age'])))

                unknown_attr = UnknownDOBAttribute.objects.filter(household_member=saved_member)
                self.assertEqual(1, unknown_attr.count())
                self.assertEqual('MONTH', unknown_attr[0].type)


    def test_invalid_answer_prefix_is_not_carried_on_when_session_time_out_or_cancelled(self):
        some_age = 10
        answers = {'name': 'dummy name',
                   'age': some_age,
                   'gender': '1',
                   'month': '2',
                   'year': datetime.datetime.now().year - some_age
        }

        with patch.object(Survey, "currently_open_survey", return_value=self.open_survey):
            mock_filter = MagicMock()
            mock_filter.exists.return_value = True
            with patch.object(RandomHouseHoldSelection.objects, 'filter', return_value=mock_filter):
                self.reset_session()
                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)
                self.respond('2')
                self.respond(answers['name'])
                self.respond(answers['age'])
                invalid_month = 45
                response = self.respond(invalid_month)

                months_option_page_1 = "\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % (
                    "INVALID ANSWER: " + self.month_question.text + months_option_page_1)
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                self.reset_session()

                self.choose_menu_to_register_household()
                selected_household_id = '2'
                self.select_household(selected_household_id)

                response = self.respond('2')
                name_question = "responseString=%s&action=request" % self.question_1.text
                self.assertEquals(urllib2.unquote(response.content), name_question)

                response = self.respond(answers['name'])
                next_registration_question = "responseString=%s&action=request" % self.age_question.text
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

                response = self.respond(answers['age'])
                months_option_page_1 = "\n1: January\n2: February\n3: March\n#: Next"
                next_registration_question = "responseString=%s&action=request" % \
                                             (self.month_question.text + months_option_page_1)
                self.assertNotIn('INVALID ANSWER', urllib2.unquote(response.content))
                self.assertEquals(urllib2.unquote(response.content), next_registration_question)

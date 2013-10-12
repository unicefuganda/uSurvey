from random import randint
import datetime
import urllib2
from django.http.request import HttpRequest
from django.test import Client
from rapidsms.contrib.locations.models import Location
from survey.investigator_configs import COUNTRY_PHONE_CODE
from survey.models import Investigator, Backend, Household, Question, HouseholdMemberGroup, HouseholdHead, QuestionModule
from survey.models.households import HouseholdMember
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
        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number=self.ussd_params['msisdn'].replace(
                                                            COUNTRY_PHONE_CODE, ''),
                                                        location=Location.objects.create(name="Kampala"),
                                                        backend=Backend.objects.create(name='something'))

        self.household1 = self.create_household(1)
        self.household2 = self.create_household(2)
        self.household3 = self.create_household(3)
        self.household4 = self.create_household(4)
        self.household5 = self.create_household(5)

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

    def test_should_render_first_registration_question_when_selected_member_for_registration(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        question_1 = Question.objects.create(text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)
        question_2 = Question.objects.create(text="Please Enter the age",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        self.reset_session()
        self.register_household()
        self.select_household("2")
        response = self.respond('2')
        first_registration_question = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), first_registration_question)

    def test_should_render_next_registration_question_when_answered_one(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        question_1 = Question.objects.create(text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)
        question_2 = Question.objects.create(text="Please Enter the age",
                                             answer_type=Question.NUMBER, order=2, group=self.registration_group)

        self.reset_session()
        self.register_household()
        self.select_household("2")
        self.respond('2')
        response = self.respond('Dummy name')
        next_registration_question = "responseString=%s&action=request" % question_2.text
        self.assertEquals(urllib2.unquote(response.content), next_registration_question)

    def test_should_render_third_registration_question_when_answered_two(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age",
                                             answer_type=Question.TEXT, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

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
                   'gender':'2'
                   }
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age",
                                             answer_type=Question.TEXT, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

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
        self.assertEqual(member.male,False)


    def test_should_know_if_question_is_gender_question(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        question = Question.objects.create(text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)
        ussd_register = USSDRegisterHousehold(self.investigator, FakeRequest())
        self.assertTrue(ussd_register.is_gender_question(question))

    def test_should_know_if_question_is_age_question(self):
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)
        module = QuestionModule.objects.create(name='Registration')

        question = Question.objects.create(text="Please Enter the age",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)
        ussd_register = USSDRegisterHousehold(self.investigator, FakeRequest())
        self.assertTrue(ussd_register.is_age_question(question))


    def test_should_save_household_head_object(self):
        answers = {'name': 'dummy name',
                   'age': '10',
                   'gender':'1'
                   }
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age",
                                             answer_type=Question.TEXT, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)


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
                   'gender':'1'
                   }
        self.registration_group = self.member_group = HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)

        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age",
                                             answer_type=Question.TEXT, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)


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
        ask_member_response_string = "responseString=%s&action=request" % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER']
        self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)


    def test_should_go_back_to_welcome_screen_if_responds_no_after_registering_a_member(self):
        answers = {'name': 'dummy name',
                   'age': '10',
                   'gender':'1'
                   }
        self.registration_group =  HouseholdMemberGroup.objects.create(name="REGISTRATION GROUP", order=0)
        module = QuestionModule.objects.create(name='Registration')

        question_1 = Question.objects.create(module=module, text="Please Enter the name",
                                             answer_type=Question.TEXT, order=1, group=self.registration_group)

        question_2 = Question.objects.create(module=module, text="Please Enter the age",
                                             answer_type=Question.TEXT, order=2, group=self.registration_group)

        question_3 = Question.objects.create(module=module, text="Please Enter the gender: 1.Male\n2.Female",
                                             answer_type=Question.NUMBER, order=3, group=self.registration_group)

        self.reset_session()
        self.register_household()
        selected_household_id = '2'
        self.select_household(selected_household_id)
        self.respond('1')
        self.respond(answers['name'])
        self.respond(answers['age'])
        self.respond(answers['gender'])

        response = self.respond('2')
        ask_member_response_string = "responseString=%s&action=request" % USSD.MESSAGES['WELCOME_TEXT']
        self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)

    def test_should_ask_member_question_after_registering_head_if_investigator_responds_with_yes_to_register_other_members(self):

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
        self.reset_session()
        self.register_household()
        selected_household_id = '2'
        self.select_household(selected_household_id)
        self.respond('1')
        self.respond(answers['name'])
        self.respond(answers['age'])
        self.respond(answers['gender'])

        response = self.respond('1')
        first_registration_question = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), first_registration_question)

    def test_complete_registration_flow(self):

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
        self.reset_session()
        self.register_household()
        selected_household_id = '2'
        self.select_household(selected_household_id)
        self.respond('2')
        self.respond(answers['name'])
        self.respond(answers['age'])
        self.respond(answers['gender'])

        response = self.respond('1')
        select_head_or_member = "responseString=%s&action=request" % USSD.MESSAGES['SELECT_HEAD_OR_MEMBER']
        self.assertEquals(urllib2.unquote(response.content), select_head_or_member)
        response = self.respond('1')
        first_registration_question = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), first_registration_question)
        self.respond(answers['name'])
        self.respond(answers['age'])
        self.respond(answers['gender'])

        response = self.respond('1')
        first_registration_question = "responseString=%s&action=request" % question_1.text
        self.assertEquals(urllib2.unquote(response.content), first_registration_question)
        self.respond(answers['name'])
        self.respond(answers['age'])
        self.respond(answers['gender'])

        response = self.respond('2')
        ask_member_response_string = "responseString=%s&action=request" % USSD.MESSAGES['WELCOME_TEXT']
        self.assertEquals(urllib2.unquote(response.content), ask_member_response_string)


class FakeRequest(HttpRequest):

    def dict(self):
        obj = self.__dict__
        obj['transactionId'] = '1234567890'
        obj['response'] = 'false'
        return obj
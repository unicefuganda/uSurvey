from random import randint
import datetime
from django.http import HttpRequest
from django.test.testcases import TestCase
from survey.models import NumericalAnswer, Question, QuestionOption, QuestionModule, HouseholdMemberGroup
from mock import patch


class USSDBaseTest(TestCase):
    def setUp(self):
        self.ussd_params = {
            'transactionId': "123344" + str(randint(1, 99999)),
            'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
            'msisdn': '2567765' + str(randint(1, 99999)),
            'ussdServiceCode': '130',
            'ussdRequestString': '',
            'response': "false"
        }

    def test_ussd_parameters_set_up(self):
        self.assertEqual('false', self.ussd_params['response'])
        self.assertEqual('', self.ussd_params['ussdRequestString'])
        self.assertEqual('130', self.ussd_params['ussdServiceCode'])

    def reset_session(self):
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))
        self.ussd_params['response'] = 'false'
        self.ussd_params['ussdRequestString'] = ''
        return self.client.post('/ussd', data=self.ussd_params)

    def select_samples(self):
        self.ussd_params['transactionId'] = "123344" + str(randint(1, 99999))
        self.ussd_params['response'] = 'false'
        self.ussd_params['ussdRequestString'] = ''
        self.client.post('/ussd', data=self.ussd_params)

        self.ussd_params['response'] = 'true'
        self.ussd_params['ussdRequestString'] = '100'
        return self.client.post('/ussd', data=self.ussd_params)

    def choose_menu_to_register_household(self):
        return self.respond('1')

    def choose_menu_to_take_survey(self):
        return self.respond("2")

    def choose_menu_to_report_non_response(self):
        return self.respond('3')

    def select_household(self, household_id="1"):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = household_id
        return self.client.post('/ussd', data=self.ussd_params)

    def select_household_member(self, member_id="1"):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = member_id
        return self.client.post('/ussd', data=self.ussd_params)

    def respond(self, message):
        self.ussd_params['response'] = "true"
        self.ussd_params['ussdRequestString'] = message
        return self.client.post('/ussd', data=self.ussd_params)

    def set_questions_answered_to_twenty_minutes_ago(self):
        for answer in NumericalAnswer.objects.all():
            answer.created -= datetime.timedelta(minutes=(20), seconds=1)
            answer.save()

    def hh_string(self, household_head):
        return "HH-%s-%s" % (household_head.household.random_sample_number, household_head.surname)

    def mock_date_today(self, target, real_date_class=datetime.date):
        class DateSubclassMeta(type):
            @classmethod
            def __instancecheck__(mcs, obj):
                return isinstance(obj, real_date_class)

        class BaseMockedDate(real_date_class):
            @classmethod
            def today(cls):
                return target

        # Python2 & Python3 compatible metaclass
        MockedDate = DateSubclassMeta('date', (BaseMockedDate,), {})

        return patch.object(datetime, 'date', MockedDate)

    def generate_register_HH_questions(self):
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


class FakeRequest(HttpRequest):
    def dict(self):
        obj = self.__dict__
        obj['transactionId'] = '1234567890'
        obj['response'] = 'false'
        return obj

    def __setitem__(self, key, value):
        obj = self.__dict__
        obj[key] = value
        return obj
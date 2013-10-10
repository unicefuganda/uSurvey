# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import date
import dateutils
from django.core.exceptions import ObjectDoesNotExist
from survey.models import Question, HouseholdHead
from survey.models.households import HouseholdMember
from survey.ussd.ussd import USSD


class USSDRegisterHousehold(USSD):
    HEAD_ANSWER = {
        'HEAD':'1',
        'MEMBER':'2'
    }
    REGISTRATION_DICT = {}

    def __init__(self, investigator, request):
        super(USSDRegisterHousehold, self).__init__(investigator, request)
        self.question = None
        self.is_head = None
        self.set_question()
        self.set_form_in_cache()
        self.set_household()
        self.set_household_member()
        self.set_head_in_cache()

    def set_question(self):
        try:
            question = self.get_from_session('QUESTION')
            if question:
                self.question = question
        except KeyError:
            pass

    def set_form_in_cache(self):
        if not self.investigator.get_from_cache('registration_dict'):
            self.investigator.set_in_cache('registration_dict', self.REGISTRATION_DICT)

    def set_head_in_cache(self):
        if not self.investigator.get_from_cache('is_head'):
            self.investigator.set_in_cache('is_head', self.is_head)

    def set_head(self,answer):
        if self.is_head is not None:
            if answer == self.HEAD_ANSWER['HEAD']:
                self.is_head = True
            else:
                self.is_head = False

    def start(self, answer):
        self.register_households(answer)
        self.set_in_session('QUESTION', self.question)
        return self.action, self.responseString

    def register_households(self, answer):
        if self.is_browsing_households_list(answer):
            self.get_household_list()
        elif self.household:
            self.set_head(answer)
            response = self.render_registration_questions(answer)
            if not response is None:
                self.responseString = response
        else:
            self.select_household(answer)
            self.render_select_member_or_head()

    def render_select_member_or_head(self):
        self.responseString = self.MESSAGES['SELECT_HEAD_OR_MEMBER']

    def render_welcome_screen(self):
        self.responseString = self.MESSAGES['WELCOME_TEXT']

    def render_registration_questions(self, answer):
        if self.household_member:
            if answer == self.ANSWER['YES']:
                self.render_select_member_or_head()
            if answer == self.ANSWER['NO']:
                self.render_welcome_screen()
            self.set_in_session('HOUSEHOLD_MEMBER',None)
        else:
            all_questions = Question.objects.filter(group__name="REGISTRATION GROUP").order_by('order')
            if not self.question:
                self.question = all_questions[0]
            else:
                self.question = self.process_registration_answer(answer)
            return self.question.text if self.question else None

    def process_registration_answer(self, answer):
        try:
            next_question = self.question.get_next_question_by_rule(answer, self.investigator)
            if next_question != self.question:
                self.REGISTRATION_DICT[self.question.text] = answer
                self.investigator.set_in_cache('registration_dict', self.REGISTRATION_DICT)

        except ObjectDoesNotExist, e:
            self.REGISTRATION_DICT[self.question.text] = answer
            self.investigator.set_in_cache('registration_dict', self.REGISTRATION_DICT)
            next_question = self.get_next_registration_question()

        return next_question

    def get_next_registration_question(self):
        next_questions = Question.objects.filter(group__name="REGISTRATION GROUP", order__gte=self.question.order + 1)
        if next_questions:
            return next_questions[0]
        else:
            self.save_member_object()
            self.responseString = USSD.MESSAGES['END_REGISTRATION']

    def save_member_object(self):
        member_dict = {}
        member_fields = ['surname', 'date_of_birth', 'male']
        all_questions = Question.objects.filter(group__name="REGISTRATION GROUP").order_by('order')

        count = 0
        for question in all_questions:
            if self.is_age_question(question):
                self.REGISTRATION_DICT[question.text] = self.format_age_to_date_of_birth(question)

            if self.is_gender_question(question):
                self.REGISTRATION_DICT[question.text] = self.format_gender_response(question)
            member_dict[member_fields[count]] = self.REGISTRATION_DICT[question.text]
            count += 1
        member_dict['household'] = self.household
        if not self.is_head:
            object_to_create = HouseholdMember
        else:
            object_to_create = HouseholdHead
        member = object_to_create.objects.create(**member_dict)
        self.set_in_session('HOUSEHOLD_MEMBER',member)

    def format_age_to_date_of_birth(self, question):
        age = self.REGISTRATION_DICT[question.text]
        date_of_birth = dateutils.increment(date.today(), years=-int(age))
        return date_of_birth

    def format_gender_response(self,question):
        response = self.REGISTRATION_DICT[question.text]
        if response == '1':
            return True
        return False

    def is_age_question(self, question):
        return question.text.lower() == 'please enter the age'

    def is_gender_question(self, question):
        return question.text.lower().startswith('please enter the gender')
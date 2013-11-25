# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import date, datetime
from django.core.exceptions import ObjectDoesNotExist
from survey.models import Question, HouseholdHead
from survey.models.households import HouseholdMember
from survey.ussd.ussd import USSD


class USSDRegisterHousehold(USSD):
    HEAD_ANSWER = {
        'HEAD': '1',
        'MEMBER': '2'
    }
    REGISTRATION_DICT = {}

    UNKNOWN_AGE = 0

    def __init__(self, investigator, request):
        super(USSDRegisterHousehold, self).__init__(investigator, request)
        self.question = None
        self.household_member = None
        self.is_head = None
        self.is_selecting_member = False
        self.set_question()
        self.set_form_in_cache()
        self.set_household()
        self.set_household_member()
        self.set_head_in_cache()
        self.set_is_selecting_member()

    def set_question(self):
        try:
            question = self.get_from_session('QUESTION')
            if question:
                self.question = question
        except KeyError:
            pass

    def set_form_in_cache(self):
        try:
            if not self.investigator.get_from_cache('registration_dict'):
                self.investigator.set_in_cache('registration_dict', self.REGISTRATION_DICT)
            else:
                self.REGISTRATION_DICT = self.investigator.get_from_cache('registration_dict')
        except KeyError:
            pass

    def set_head_in_cache(self):
        try:
            is_head = self.investigator.get_from_cache('is_head')
            if is_head is not None:
                self.is_head = is_head
        except KeyError:
            pass

    def set_is_selecting_member(self):
        try:
            is_selecting_member = self.investigator.get_from_cache('is_selecting_member')
            if is_selecting_member is not None:
                self.is_selecting_member = is_selecting_member
        except KeyError:
            self.investigator.set_in_cache('is_selecting_member', False)

    def set_head(self, answer):
        if self.is_head is None or not self.is_head:
            if answer == self.HEAD_ANSWER['HEAD']:
                self.investigator.set_in_cache('is_head', True)
            else:
                self.investigator.set_in_cache('is_head', False)
        self.is_head = self.investigator.get_from_cache('is_head')
        self.investigator.set_in_cache('is_selecting_member', False)

    def start(self, answer):
        self.register_households(answer)
        self.set_in_session('QUESTION', self.question)
        return self.action, self.responseString

    def render_questions_based_on_head_selection(self, answer):
        if self.household.get_head():
            self.render_questions_or_member_selection(answer)
        else:
            self.render_select_member_or_head()

    def validate_house_selection(self):
        if self.is_invalid_response():
            self.get_household_list()
        else:
            self.investigator.set_in_cache('HOUSEHOLD', self.household)

    def register_households(self, answer):
        if not self.household and self.is_browsing_households_list(answer):
            self.get_household_list()
        elif self.household:
            if self.is_selecting_member:
                self.set_head(answer)
            response = self.render_registration_options(answer)
            if not response is None:
                self.responseString += response
        else:
            if not self.is_resuming_survey:
                self.select_household(answer)
                self.validate_house_selection()
            else:
                self.household = self.investigator.get_from_cache('HOUSEHOLD')

            if self.household:
                self.render_questions_based_on_head_selection(answer)

    def render_select_member_or_head(self):
        self.investigator.set_in_cache('is_selecting_member', True)
        self.responseString = self.MESSAGES['SELECT_HEAD_OR_MEMBER'] % str(self.household.random_sample_number)

    def render_welcome_screen(self):
        self.responseString = self.MESSAGES['WELCOME_TEXT'] % self.investigator.name

    def render_questions_or_member_selection(self, answer):

        if self.household.get_head():
            self.investigator.set_in_cache('is_head', False)
            self.responseString = USSD.MESSAGES['HEAD_REGISTERED']
            self.responseString += self.render_questions(answer)

        else:
            self.render_select_member_or_head()

    def render_questions(self, answer):
        all_questions = Question.objects.filter(group__name="REGISTRATION GROUP").order_by('order')

        if not self.question:
            self.question = all_questions[0]
        else:
            self.question = self.process_registration_answer(answer)

        page = self.get_from_session('PAGE')
        self.add_question_prefix()
        return self.question.to_ussd(page) if self.question else None

    def render_registration_options(self, answer):
        if self.household_member:
            if answer == self.ANSWER['YES']:
                self.household = self.investigator.get_from_cache('HOUSEHOLD')
                self.render_questions_or_member_selection(answer)
            if answer == self.ANSWER['NO']:
                self.investigator.clear_interview_caches()
                self.set_in_session('HOUSEHOLD', None)
                self.render_welcome_screen()
            self.set_in_session('HOUSEHOLD_MEMBER', None)

        else:
            return self.render_questions(answer)

    def process_registration_answer(self, answer):
        answer = int(answer) if answer.isdigit() else answer

        if not answer and answer != 0:
            self.investigator.invalid_answer(self.question)
            return self.question

        if self.question.is_multichoice() and self.is_pagination_option(answer):
            self.set_current_page(answer)
            self.investigator.remove_ussd_variable('INVALID_ANSWER', self.question)
            return self.question

        age_question = Question.objects.get(text__startswith="Please Enter the age")
        if self.is_year_question_answered() and not self.age_validates(answer):
            self.investigator.invalid_answer(age_question)
            return age_question

        try:
            answer_class = self.question.answer_class()
            if self.question.is_multichoice():
                answer = self.question.get_option(answer, self.investigator)
                if not answer:
                    return self.question

            _answer = answer_class(answer=answer)
            next_question = self.question.get_next_question_by_rule(_answer, self.investigator)
            if next_question != self.question:
                next_question.order = self.question.order
                self.REGISTRATION_DICT[self.question.text] = answer
                self.investigator.set_in_cache('registration_dict', self.REGISTRATION_DICT)

        except ObjectDoesNotExist, e:
            self.REGISTRATION_DICT[self.question.text] = answer
            self.investigator.set_in_cache('registration_dict', self.REGISTRATION_DICT)
            next_question = self.get_next_registration_question()

        return next_question

    def get_next_registration_question(self):
        next_questions = Question.objects.filter(group__name="REGISTRATION GROUP",
                                                 order__gte=self.question.order + 1).order_by('order')
        if next_questions:
            return next_questions[0]
        else:
            self.save_member_object()
            self.investigator.clear_all_cache_fields_except('IS_REGISTERING_HOUSEHOLD')
            self.investigator.set_in_cache('HOUSEHOLD', self.household)
            self.responseString = USSD.MESSAGES['END_REGISTRATION']

    def save_member_object(self):
        member_dict = {}
        name_question = Question.objects.get(text__startswith="Please Enter the name")
        age_question = Question.objects.get(text__startswith="Please Enter the age")
        gender_question = Question.objects.get(text__startswith="Please Enter the gender")

        member_dict['surname'] = self.REGISTRATION_DICT[name_question.text]
        member_dict['male'] = self.format_gender_response(gender_question)

        if self.REGISTRATION_DICT[age_question.text] == self.UNKNOWN_AGE:
            month_of_birth_question = Question.objects.get(text__startswith="Please Enter the month of birth")
            year_of_birth_question = Question.objects.get(text__startswith="Please Enter the year of birth")
            member_dict['date_of_birth'] = self.get_date_of_birth_from(year_of_birth_question, month_of_birth_question)
        else:
            member_dict['date_of_birth'] = self.format_age_to_date_of_birth(age_question)

        object_to_create = HouseholdHead if self.is_head else HouseholdMember
        member = object_to_create.objects.create(surname=member_dict['surname'], male=member_dict['male'],
                                                 date_of_birth=member_dict['date_of_birth'], household=self.household)
        self.set_in_session('HOUSEHOLD_MEMBER', member)

    def format_age_to_date_of_birth(self, question):
        age = self.REGISTRATION_DICT[question.text]
        today = date.today()
        date_of_birth = today.replace(year=(today.year - int(age)))
        return date_of_birth

    def format_gender_response(self, question):
        return self.REGISTRATION_DICT[question.text] == 1

    def get_date_of_birth_from(self, year_of_birth_question, month_of_birth_question):
        year = int(self.REGISTRATION_DICT[year_of_birth_question.text])
        month = self.REGISTRATION_DICT[month_of_birth_question.text].order
        return datetime(year, month, 1)

    def is_year_question_answered(self):
        return "year of birth" in self.question.text

    def age_validates(self, answer):
        age_question = Question.objects.get(text__startswith="Please Enter the age")
        given_age = self.REGISTRATION_DICT[age_question.text]
        inferred_year_of_birth = date.today().year - int(given_age)
        return inferred_year_of_birth == int(answer)
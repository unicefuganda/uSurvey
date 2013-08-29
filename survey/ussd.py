from django.core.cache import cache
from django.conf import settings
from survey.models_file import RandomHouseHoldSelection
from survey.investigator_configs import *


class USSDBase(object):
    MESSAGES = {
        'SUCCESS_MESSAGE': "This survey has come to an end. Your responses have been received. Thank you.",
        'BATCH_5_MIN_TIMEDOUT_MESSAGE': "This batch is already completed and 5 minutes have passed. You may no longer retake it.",
        'USER_NOT_REGISTERED': "Sorry, your mobile number is not registered for this survey",
        'WELCOME_TEXT': "Welcome %s to the survey.",
        'HOUSEHOLD_LIST': "Please select a household from the list",
        'SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS': "The survey is now complete. Please collect your salary from the district coordinator.",
        'RETAKE_SURVEY': "You have already completed this household. Would you like to start again?\n1: Yes\n2: No",
        'NO_HOUSEHOLDS': "Sorry, you have no households registered.",
        'NO_OPEN_BATCH': "Sorry, there are no open surveys currently.",
        'HOUSEHOLDS_COUNT_QUESTION': "How many households have you listed in your segment?",
        'HOUSEHOLD_SELECTION_SMS_MESSAGE': "Thank you. You will receive the household numbers selected for your segment",
        'HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE': "Count must be greater than %s. How many households have you listed in your segment?" % NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR,
    }

    ACTIONS = {
        'REQUEST': 'request',
        'END': 'end'
    }

    DEFAULT_SESSION_VARIABLES = {
        'PAGE': 1,
        'HOUSEHOLD': None
    }

    HOUSEHOLD_LIST_OPTION = "00"

    TIMEOUT_MINUTES = 5

    def is_new_request(self):
        return self.request['response'] == 'false'


class USSD(USSDBase):
    def __init__(self, investigator, request):
        super(USSD, self).__init__()
        self.investigator = investigator
        self.request = request.dict()
        self.action = self.ACTIONS['REQUEST']
        self.responseString = ""
        self.household = None
        self.set_session()
        self.set_household()
        self.clean_investigator_input()

    def set_household(self):
        household = self.get_from_session('HOUSEHOLD')
        if household:
            self.household = household
        elif self.is_active():
            last_answered = self.investigator.last_answered()
            if last_answered:
                household = last_answered.household
                if household.next_question():
                    self.household = household

    def set_session(self):
        self.session_string = "SESSION-%s" % self.request['transactionId']
        if not cache.get(self.session_string):
            cache.set(self.session_string, self.DEFAULT_SESSION_VARIABLES)

    def get_from_session(self, key):
        return cache.get(self.session_string)[key]

    def set_in_session(self, key, value):
        session = cache.get(self.session_string)
        session[key] = value
        cache.set(self.session_string, session)

    def is_pagination_option(self, answer):
        return answer in getattr(settings, 'USSD_PAGINATION', None).values()

    def is_pagination(self, question, answer):
        pagination = False
        if question.is_multichoice():
            pagination = self.is_pagination_option(answer)
        if not pagination:
            self.set_in_session('PAGE', self.DEFAULT_SESSION_VARIABLES['PAGE'])
        return pagination

    def set_current_page(self, answer):
        current_page = self.get_from_session('PAGE')
        if answer == getattr(settings, 'USSD_PAGINATION', None).get('PREVIOUS'):
            current_page -= 1
        elif answer == getattr(settings, 'USSD_PAGINATION', None).get('NEXT'):
            current_page += 1
        self.set_in_session('PAGE', current_page)

    def question_present_in_cache(self, label):
        return self.question in self.investigator.get_from_cache(label)

    def reanswerable_question(self):
        return self.question_present_in_cache('REANSWER')

    def invalid_answered_question(self):
        return self.question_present_in_cache('INVALID_ANSWER')

    def process_investigator_response(self):
        answer = self.request['ussdRequestString'].strip()
        if not answer:
            return self.investigator.invalid_answer(self.question)
        if self.is_pagination(self.question, answer):
            self.set_current_page(answer)
        else:
            self.question = self.investigator.answered(self.question, self.household, answer)

    def add_question_prefix(self):
        if self.reanswerable_question():
            self.responseString += "RECONFIRM: "
        if self.invalid_answered_question():
            self.responseString += "INVALID ANSWER: "

    def end_interview(self):
        self.action = self.ACTIONS['END']
        if self.investigator.completed_open_surveys():
            self.responseString = USSD.MESSAGES['SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS']
        elif not self.household.can_retake_survey(batch=self.get_current_batch(), minutes=self.TIMEOUT_MINUTES):
            self.responseString = USSD.MESSAGES['BATCH_5_MIN_TIMEDOUT_MESSAGE']
        else:
            self.responseString = USSD.MESSAGES['SUCCESS_MESSAGE']

        self.investigator.clear_interview_caches()

    def render_survey_response(self):
        if not self.question:
            self.end_interview()
        else:
            page = self.get_from_session('PAGE')
            self.add_question_prefix()
            self.responseString += self.question.to_ussd(page)

    def get_current_batch(self):
        if not self.household.survey_completed():
            return self.question.batch
        if self.household:
            return self.household.last_question_answered().batch
        return self.investigator.first_open_batch()

    def render_survey(self):
        if not self.household.survey_completed():
            self.question = self.household.next_question()

            if not self.is_new_request():
                self.process_investigator_response()
            self.render_survey_response()
        elif self.household.can_retake_survey(batch=self.get_current_batch(), minutes=self.TIMEOUT_MINUTES):
            self.retake_survey()
        else:
            self.end_interview()

    def confirm_retake_survey(self, answer):
        try:
            answer = int(answer)
            return answer == 1
        except ValueError, e:
            return False

    def retake_survey(self):
        answer = self.request['ussdRequestString'].strip()
        if not answer:
            self.responseString = self.MESSAGES['RETAKE_SURVEY']
        else:
            if self.confirm_retake_survey(answer):
                self.household.retake_latest_batch()
                self.behave_like_new_request()
                self.render_survey()
            else:
                self.household = None
                self.set_in_session('HOUSEHOLD', self.household)
                self.render_households_list(self.HOUSEHOLD_LIST_OPTION)

    def render_welcome_text(self):
        if self.investigator.has_households():
            welcome_message = self.MESSAGES['WELCOME_TEXT'] % self.investigator.name
            self.responseString = "%s\n%s: Households list" % (welcome_message, self.HOUSEHOLD_LIST_OPTION)
        else:
            self.action = self.ACTIONS['END']
            self.responseString = self.MESSAGES['NO_HOUSEHOLDS']

    def is_browsing_households_list(self, answer):
        if answer == self.HOUSEHOLD_LIST_OPTION or self.is_pagination_option(answer):
            self.set_current_page(answer)
            return True

    def select_household(self, answer):
        try:
            answer = int(answer)
            self.household = self.investigator.all_households()[answer - 1]
            self.set_in_session('HOUSEHOLD', self.household)
        except (ValueError, IndexError) as e:
            self.responseString += "INVALID SELECTION: "

    def render_households_list(self, answer):
        if not self.is_browsing_households_list(answer):
            self.select_household(answer)
        if not self.household:
            page = self.get_from_session('PAGE')
            self.responseString += "%s\n%s" % (self.MESSAGES['HOUSEHOLD_LIST'], self.investigator.households_list(page))
        else:
            self.behave_like_new_request()
            self.render_survey()

    def render_homepage(self):

        answer = self.request['ussdRequestString'].strip()
        if not answer:
            self.render_welcome_text()
        else:
            self.render_households_list(answer)

    def has_chosen_household(self):
        return self.household is not None

    def is_active(self):
        return self.investigator.was_active_within(self.TIMEOUT_MINUTES)

    def process_open_batch(self):
        if self.has_chosen_household():
            self.render_survey()
        else:
            self.render_homepage()

    def show_message_for_no_open_batch(self):
        self.action = self.ACTIONS['END']
        self.responseString = self.MESSAGES['NO_OPEN_BATCH']

    def response(self):
        if self.investigator.has_open_batch():
            self.process_open_batch()
        else:
            self.show_message_for_no_open_batch()
        return {'action': self.action, 'responseString': self.responseString}

    def clean_investigator_input(self):
        if self.is_new_request():
            self.request['ussdRequestString'] = ''

    def behave_like_new_request(self):
        self.request['ussdRequestString'] = ""
        self.request['response'] = 'false'

    @classmethod
    def investigator_not_registered_response(self):
        return {'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['USER_NOT_REGISTERED']}


class HouseHoldSelection(USSDBase):
    def __init__(self, mobile_number, request):
        super(HouseHoldSelection, self).__init__()
        self.mobile_number = mobile_number
        self.request = request

    def randomly_select_households(self):
        no_of_households = int(self.request['ussdRequestString'].strip())
        if no_of_households >= NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR:
            RandomHouseHoldSelection.objects.get_or_create(mobile_number=self.mobile_number)[0].generate(
                no_of_households=no_of_households)
            return {'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['HOUSEHOLD_SELECTION_SMS_MESSAGE']}
        else:
            return {'action': self.ACTIONS['REQUEST'],
                    'responseString': self.MESSAGES['HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE']}

    def response(self):
        if self.is_new_request():
            return {'action': self.ACTIONS['REQUEST'], 'responseString': self.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']}
        else:
            return self.randomly_select_households()
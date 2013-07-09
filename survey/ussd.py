from django.core.cache import cache
from django.conf import settings

class USSD(object):
    MESSAGES = {
        'SUCCESS_MESSAGE': "This survey has come to an end. Your responses have been received. Thank you.",
        'USER_NOT_REGISTERED': "Sorry, your mobile number is not registered for this survey",
        'WELCOME_TEXT': "Welcome %s to the survey.",
        'HOUSEHOLD_LIST': "Please select a household from the list",
        'SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS': "The survey is now complete. Please collect your salary from the district coordinator.",
        'RETAKE_SURVEY': "You have already completed this household. Would you like to start again?\n1: Yes\n2: No",
        'NO_HOUSEHOLDS': "Sorry, you have no households registered.",
        'NO_OPEN_BATCH': "Sorry, there are no open surveys currently.",
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
        return answer in getattr(settings,'USSD_PAGINATION',None).values()

    def is_pagination(self, question, answer):
        pagination = False
        if question.is_multichoice():
            pagination = self.is_pagination_option(answer)
        if not pagination:
            self.set_in_session('PAGE', self.DEFAULT_SESSION_VARIABLES['PAGE'])
        return pagination

    def set_current_page(self, answer):
        current_page = self.get_from_session('PAGE')
        if answer == getattr(settings,'USSD_PAGINATION',None).get('PREVIOUS'):
            current_page -= 1
        elif answer == getattr(settings,'USSD_PAGINATION',None).get('NEXT'):
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
        self.responseString = USSD.MESSAGES['SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS'] if self.investigator.completed_open_surveys() else USSD.MESSAGES['SUCCESS_MESSAGE']
        self.investigator.clear_interview_caches()

    def render_survey_response(self):
        if not self.question:
            self.end_interview()
        else:
            page = self.get_from_session('PAGE')
            self.add_question_prefix()
            self.responseString += self.question.to_ussd(page)

    def render_survey(self):
        if not self.household.survey_completed():
            self.question = self.household.next_question()
            if not self.is_new_request():
                self.process_investigator_response()
            self.render_survey_response()
        else:
            self.retake_survey()

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
        return self.household != None

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
        return { 'action': self.action, 'responseString': self.responseString }

    def is_new_request(self):
        return self.request['response'] == 'false'

    def clean_investigator_input(self):
        if self.is_new_request():
            self.request['ussdRequestString'] = ''

    def behave_like_new_request(self):
        self.request['ussdRequestString'] = ""
        self.request['response'] = 'false'

    @classmethod
    def investigator_not_registered_response(self):
        return { 'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['USER_NOT_REGISTERED'] }
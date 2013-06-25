from django.core.cache import cache
from django.conf import settings

class USSD(object):
    MESSAGES = {
        'SUCCESS_MESSAGE': "This survey has come to an end. Your responses have been received. Thank you.",
        'USER_NOT_REGISTERED': "Sorry, your mobile number is not registered for this survey",
        'WELCOME_TEXT': "Welcome %s to the survey. You will recieve refund only on the completion of the survey.",
        'HOUSEHOLD_LIST': "Please select an household from the list",
        'SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS': "BLAH BLAH",
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

    def __init__(self, investigator, request):
        super(USSD, self).__init__()
        self.investigator = investigator
        self.request = request
        self.action = self.ACTIONS['REQUEST']
        self.responseString = ""
        self.household = None
        self.set_session()
        self.set_household()

    def set_household(self):
        household = self.get_from_session('HOUSEHOLD')
        if household:
            self.household = household
        else:
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

    def merge_ussd_session_variables(self):
        pass

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
            self.responseString += "Reconfirm: "
        if self.invalid_answered_question():
            self.responseString += "INVALID ANSWER: "

    def render_survey_response(self):
        if not self.question:
            self.action = self.ACTIONS['END']
            self.responseString = USSD.MESSAGES['SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS'] if self.investigator.completed_open_surveys() else USSD.MESSAGES['SUCCESS_MESSAGE']
        else:
            page = self.get_from_session('PAGE')
            self.add_question_prefix()
            self.responseString += self.question.to_ussd(page)

    def render_survey(self):
        self.question = self.household.next_question()
        if not self.is_new_request():
            self.process_investigator_response()
        self.merge_ussd_session_variables()
        self.render_survey_response()

    def render_welcome_text(self):
        welcome_message = self.MESSAGES['WELCOME_TEXT'] % self.investigator.name
        self.responseString = "%s\n%s: Households list" % (welcome_message, self.HOUSEHOLD_LIST_OPTION)

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

    def response(self):
        if self.household:
            self.render_survey()
        else:
            self.render_homepage()
        return { 'action': self.action, 'responseString': self.responseString }

    def is_new_request(self):
        return self.request['response'] == 'false'

    def behave_like_new_request(self):
        self.request['ussdRequestString'] = ""
        self.request['response'] = 'false'

    @classmethod
    def investigator_not_registered_response(self):
        return { 'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['USER_NOT_REGISTERED'] }
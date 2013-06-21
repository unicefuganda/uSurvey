from django.core.cache import cache
from django.conf import settings

class USSD(object):
    MESSAGES = {
        'SUCCESS_MESSAGE': "This survey has come to an end. Your responses have been received. Thank you.",
        'USER_NOT_REGISTERED': "Sorry, your mobile number is not registered for this survey"
    }

    ACTIONS = {
        'REQUEST': 'request',
        'END': 'end'
    }

    DEFAULT_SESSION_VARIABLES = {
        'PAGE': 1,
        'INVESTIGATOR_VARIABLES': {
            'REANSWER': [],
            'INVALID_ANSWER': [],
        }
    }

    def __init__(self, investigator, request):
        super(USSD, self).__init__()
        self.investigator = investigator
        self.request = request
        self.action = self.ACTIONS['REQUEST']
        self.responseString = ""
        self.set_session()
        self.household = self.investigator.households.latest('created')
        self.question = self.investigator.next_answerable_question()
        self.investigator.ussd_variables = self.get_from_session('INVESTIGATOR_VARIABLES')

    def set_session(self):
        self.session_string = "SESSION-%s" % self.request['msisdn']
        if not cache.get(self.session_string):
            cache.set(self.session_string, self.DEFAULT_SESSION_VARIABLES)

    def get_from_session(self, key):
        return cache.get(self.session_string)[key]

    def set_in_session(self, key, value):
        session = cache.get(self.session_string)
        session[key] = value
        cache.set(self.session_string, session)

    def is_pagination(self, question, answer):
        pagination = False
        if question.is_multichoice():
            pagination = answer in getattr(settings,'USSD_PAGINATION',None).values()
        if not pagination:
            self.set_in_session('PAGE', self.DEFAULT_SESSION_VARIABLES['PAGE'])
        return pagination

    def set_current_page(self, answer):
        current_page = self.get_from_session('PAGE')
        if answer == getattr(settings,'USSD_PAGINATION',None).get('PREVIOUS'):
            current_page -= 1
        else:
            current_page += 1
        self.set_in_session('PAGE', current_page)

    def question_present_in_cache(self, label):
        return self.question in self.get_from_session('INVESTIGATOR_VARIABLES')[label]

    def reanswerable_question(self):
        return self.question_present_in_cache('REANSWER')

    def invalid_answered_question(self):
        return self.question_present_in_cache('INVALID_ANSWER')

    def merge_ussd_session_variables(self):
        self.set_in_session('INVESTIGATOR_VARIABLES', self.investigator.ussd_variables)

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
            self.responseString += "Invalid answer: "

    def render_response(self):
        if not self.question:
            self.action = self.ACTIONS['END']
            self.responseString = USSD.MESSAGES['SUCCESS_MESSAGE']
        else:
            page = self.get_from_session('PAGE')
            self.add_question_prefix()
            self.responseString += self.question.to_ussd(page)
        return { 'action': self.action, 'responseString': self.responseString }

    def response(self):
        if not self.is_new_request():
            self.process_investigator_response()
        self.merge_ussd_session_variables()
        return self.render_response()

    def is_new_request(self):
        return self.request['response'] == 'false'

    @classmethod
    def investigator_not_registered_response(self):
        return { 'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['USER_NOT_REGISTERED'] }
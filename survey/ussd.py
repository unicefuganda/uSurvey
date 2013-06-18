from django.core.cache import cache
from django.conf import settings

class USSD(object):
    MESSAGES = {
        'SUCCESS_MESSAGE': "Thanks for the survey",
        'USER_NOT_REGISTERED': "Sorry, your mobile number is not registered for this survey"
    }

    ACTIONS = {
        'REQUEST': 'request',
        'END': 'end'
    }

    DEFAULT_SESSION_VARIABLES = {
        'PAGE': 1
    }

    def __init__(self, investigator, request):
        super(USSD, self).__init__()
        self.investigator = investigator
        self.request = request
        self.action = self.ACTIONS['REQUEST']
        self.responseString = ""
        self.set_session()

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

    def is_pagination(self, question, answer):
        if question.is_multichoice():
            return answer in getattr(settings,'USSD_PAGINATION',None).values()
        else:
            return False

    def set_current_page(self, answer):
        current_page = self.get_from_session('PAGE')
        if answer == getattr(settings,'USSD_PAGINATION',None).get('PREVIOUS'):
            current_page -= 1
        else:
            current_page += 1
        self.set_in_session('PAGE', current_page)

    def response(self):
        household = self.investigator.households.latest('created')
        question = self.investigator.next_answerable_question()
        if not self.is_new_request():
            answer = self.request['ussdRequestString'].strip()
            if self.is_pagination(question, answer):
                self.set_current_page(answer)
            else:
                question = self.investigator.answered(question, household, answer)
        if not question:
            self.action = self.ACTIONS['END']
            self.responseString = USSD.MESSAGES['SUCCESS_MESSAGE']
        else:
            page = self.get_from_session('PAGE')
            self.responseString = question.to_ussd(page)
        return { 'action': self.action, 'responseString': self.responseString }

    def is_new_request(self):
        return self.request['response'] == 'false'

    @classmethod
    def investigator_not_registered_response(self):
        return { 'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['USER_NOT_REGISTERED'] }
class USSD(object):
    MESSAGES = {
        'SUCCESS_MESSAGE': "Thanks for the survey",
        'USER_NOT_REGISTERED': "Sorry, your mobile number is not registered for this survey"
    }

    ACTIONS = {
        'REQUEST': 'request',
        'END': 'end'
    }

    def __init__(self, investigator, request):
        super(USSD, self).__init__()
        self.investigator = investigator
        self.request = request
        self.action = self.ACTIONS['REQUEST']
        self.responseString = ""

    def response(self):
        household = self.investigator.households.latest('created')
        question = self.investigator.next_answerable_question()
        if not self.is_new_request():
            answer = self.request['ussdRequestString']
            question = self.investigator.answered(question, household, answer)
        if not question:
            self.action = self.ACTIONS['END']
            self.responseString = USSD.MESSAGES['SUCCESS_MESSAGE']
        else:
            self.responseString = question.to_ussd
        return { 'action': self.action, 'responseString': self.responseString }

    def is_new_request(self):
        return self.request['response'] == 'false'

    @classmethod
    def investigator_not_registered_response(self):
        return { 'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['USER_NOT_REGISTERED'] }
class USSD(object):
    SUCCESS_MESSAGE = "Thanks for the survey"

    def __init__(self, investigator, request):
        super(USSD, self).__init__()
        self.investigator = investigator
        self.request = request
        self.action = "request"
        self.responseString = ""

    def response(self):
        question = self.investigator.next_answerable_question()
        if not self.is_new_request():
            answer = self.get_answer()
            question = self.investigator.answered(question, answer)
        if not question:
            self.action = "end"
            self.responseString = USSD.SUCCESS_MESSAGE
        else:
            self.responseString = question.to_ussd
        return { 'action': self.action, 'responseString': self.responseString }

    def is_new_request(self):
        return self.request['response'] == 'false'
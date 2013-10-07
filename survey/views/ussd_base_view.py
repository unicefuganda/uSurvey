from survey.ussd.ussd_survey import USSDSurvey
from survey.ussd.ussd_register_household import USSDRegisterHousehold

class USSDBaseView(object):

    ANSWER = {
        'YES':"1",
        'NO':"2",
        "REGISTER_HOUSEHOLD":"1",
        'TAKE_SURVEY':"2",
    }


    def __init__(self, investigator, request):
        super(USSDBaseView, self).__init__()
        self.investigator = investigator
        self.request = request.dict()
        self.ussd_survey = USSDSurvey(investigator, request)
        self.ussd_register_household = USSDRegisterHousehold(investigator, request)
        self.is_registering_household = None
        self.set_is_registering_household()

    def set_is_registering_household(self):
        self.is_registering_household = self.investigator.get_from_cache('IS_REGISTERING_HOUSEHOLD')

    def is_new_request(self):
        return self.request['response'] == 'false'



    def response(self):
        print self.is_registering_household
        answer = self.request['ussdRequestString'].strip()
        print"(((((((((((((((("
        print answer
        if not answer and self.is_new_request():
            action, responseString = self.ussd_survey.render_welcome_or_resume()

        elif self.is_registering_household is None:
            action = self.ussd_survey.ACTIONS['REQUEST']
            responseString =''
            if answer == self.ANSWER['TAKE_SURVEY']:
                self.investigator.set_in_cache('IS_REGISTERING_HOUSEHOLD', False)
                action, responseString = self.ussd_survey.start()
            elif answer == self.ANSWER['REGISTER_HOUSEHOLD']:
                self.investigator.set_in_cache('IS_REGISTERING_HOUSEHOLD', True)
                action, responseString = self.ussd_register_household.start(answer)

        elif not self.is_registering_household:
            action, responseString = self.ussd_survey.take_survey()

        else:
            action, responseString = self.ussd_register_household.start(answer)
        return {'action': action, 'responseString': responseString}

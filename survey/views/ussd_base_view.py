import re
from survey.investigator_configs import HAS_APPLICATION_CODE, APPLICATION_CODE
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
        answer = self.request['ussdRequestString'].strip()

        if self.investigator.is_blocked:
            return {'action': self.ussd_survey.ACTIONS['END'],
                    'responseString': self.ussd_survey.MESSAGES['INVESTIGATOR_BLOCKED_MESSAGE']}

        if self.is_new_request_parameter(answer) and self.is_new_request():
            action, responseString = self.ussd_survey.render_welcome_or_resume()

        elif self.is_registering_household is None:
            action = self.ussd_survey.ACTIONS['REQUEST']
            responseString = ''
            if answer == self.ANSWER['TAKE_SURVEY']:
                self.investigator.set_in_cache('IS_REGISTERING_HOUSEHOLD', False)
                action, responseString = self.ussd_survey.start()
            elif answer == self.ANSWER['REGISTER_HOUSEHOLD']:
                self.investigator.set_in_cache('IS_REGISTERING_HOUSEHOLD', True)
                action, responseString = self.ussd_register_household.start("00")
            else:
                action, responseString = self.ussd_survey.render_welcome_or_resume()

        elif not self.is_registering_household:
            action, responseString = self.ussd_survey.take_survey()

        else:
            if not self.ussd_survey.is_resuming_survey:
                action, responseString = self.ussd_register_household.start(answer)
            else:
                if answer == USSDSurvey.ANSWER['YES']:
                    action, responseString = self.ussd_register_household.start("00")
                    self.investigator.set_in_cache('IS_REGISTERING_HOUSEHOLD', True)
                else:
                    action = self.ussd_survey.ACTIONS['REQUEST']
                    responseString = USSDSurvey.MESSAGES['WELCOME_TEXT'] % self.investigator.name
                    self.investigator.clear_interview_caches()
                    self.ussd_register_household.set_in_session('HOUSEHOLD', None)
                    self.ussd_survey.set_in_session('HOUSEHOLD', None)
                self.ussd_survey.set_in_session('IS_RESUMING', False)
        return {'action': action, 'responseString': responseString}

    def is_new_request_parameter(self, answer):
        pattern = re.compile(r'\*\d+\#')
        match = re.match(pattern, answer)

        matches_short_code = False

        if HAS_APPLICATION_CODE:
            matches_short_code = (answer == APPLICATION_CODE)

        return not answer or match or matches_short_code
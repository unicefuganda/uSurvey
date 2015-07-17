# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from survey.interviewer_configs import NUMBER_OF_HOUSEHOLD_PER_INTERVIEWER
from survey.models import Survey
from survey.ussd.base import USSDBase


class HouseHoldSelection(USSDBase):
    def __init__(self, mobile_number, request):
        super(HouseHoldSelection, self).__init__()
        self.mobile_number = mobile_number
        self.request = request

    def response_for_survey_type(self, survey):
        if survey.has_sampling:
            response = {'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['HOUSEHOLD_SELECTION_SMS_MESSAGE']}
        else:
            response = {'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['HOUSEHOLD_CONFIRMATION_MESSAGE']}

        return response

    def randomly_select_households(self, survey):
        no_of_households = int(self.request['ussdRequestString'].strip())

        if no_of_households >= NUMBER_OF_HOUSEHOLD_PER_INTERVIEWER:
            return self.response_for_survey_type(survey)
        else:
            return {'action': self.ACTIONS['REQUEST'],
                    'responseString': self.MESSAGES['HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE']}

    def response(self, survey):
        if self.is_new_request():
            return {'action': self.ACTIONS['REQUEST'], 'responseString': self.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']}
        else:
            return self.randomly_select_households(survey)
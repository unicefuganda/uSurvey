# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from survey.investigator_configs import NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR
from survey.models import RandomHouseHoldSelection
from survey.ussd.base import USSDBase


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
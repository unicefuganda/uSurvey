from survey.models import Survey
from survey.ussd.ussd import USSD


class USSDReportNonResponse(USSD):

    def __init__(self, investigator, request):
        super(USSDReportNonResponse, self).__init__(investigator, request)
        self.question = None
        self.household_member = None
        self.household = None
        self.is_selecting_member = False
        self.set_household()
        self.set_household_member()
        self.set_is_selecting_member()

    def set_is_selecting_member(self):
        try:
            is_selecting_member = self.investigator.get_from_cache('is_selecting_member')
            if is_selecting_member is not None:
                self.is_selecting_member = is_selecting_member
        except KeyError:
            self.investigator.set_in_cache('is_selecting_member', False)

    def start(self, answer):
        self.report_non_response(answer)
        return self.action, self.responseString

    def report_non_response(self, answer):
        if not self.household and self.is_browsing_households_list(answer):
            self.get_household_list(non_response_reporting=True)
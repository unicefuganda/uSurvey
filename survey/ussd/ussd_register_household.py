# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from survey.ussd.ussd import USSD


class USSDRegisterHousehold(USSD):
    def __init__(self, investigator, request):
        super(USSDRegisterHousehold, self).__init__(investigator, request)


    def start(self):
        self.register_households("00")
        return self.action, self.responseString

    def register_households(self, answer):
        if self.is_pagination_option(answer):
            self.set_current_page(answer)
            self.get_household_list()
        else:
            self.get_household_list()
            self.render_select_member_or_head()

    def render_select_member_or_head(self):
        self.responseString = self.MESSAGES['SELECT_HEAD_OR_MEMBER']
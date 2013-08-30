# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from rapidsms.contrib.locations.models import Location
from survey.features.page_objects.base import PageObject
from survey.models import Investigator


class NewHouseholdMemberPage(PageObject):
    def __init__(self, browser, household):
        self.browser = browser
        self.household = household
        self.url = '/households/%d/member/new/' % household.id

    def validate_fields(self):
        self.is_text_present('Name')
        self.is_text_present('Sex')
        self.is_text_present('Date of birth')
        self.is_text_present('Create')
        self.is_text_present('Cancel')


    def fill_valid_member_values(self,data):
        self.browser.fill_form(data)
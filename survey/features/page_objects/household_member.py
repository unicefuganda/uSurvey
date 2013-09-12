# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from survey.features.page_objects.base import PageObject


class NewHouseholdMemberPage(PageObject):
    def __init__(self, browser, household):
        self.browser = browser
        self.household = household
        self.url = '/households/%d/member/new/' % household.id

    def validate_fields(self):
        self.validate_fields_present(['Family Name', 'Sex', 'Date of birth', 'Create', 'Cancel'])

    def fill_valid_member_values(self, data):
        self.browser.fill_form(data)


class EditHouseholdMemberPage(PageObject):

    def __init__(self, browser, household,member):
        self.browser = browser
        self.household = household
        self.member = member
        self.url = '/households/%d/member/%d/edit/' % (household.id,member.id)

    def validate_member_details(self, household_member):
        self.browser.is_text_present(household_member.surname)
        self.browser.is_text_present(household_member.date_of_birth)
        self.is_radio_selected('male',True)

    def fill_valid_member_values(self, data):
        self.browser.fill_form(data)


class DeleteHouseholdMemberPage(PageObject):
    def __init__(self, browser, household, member):
        self.browser = browser
        self.household = household
        self.member = member
        self.url = '/households/%d/member/%d/delete/' % (household.id, member.id)

    def see_delete_confirmation_modal(self):
        self.is_text_present("Are you sure you want to delete %s" % self.member.surname)
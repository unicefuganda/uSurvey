from survey.features.page_objects.base import PageObject
from nose.tools import assert_equals


class GroupConditionListPage(PageObject):
    url = '/conditions/'

    def validate_fields(self):
        assert_equals(True, self.browser.is_text_present('Groups Condition List'))
        assert_equals(True, self.browser.is_text_present('Condition'))
        assert_equals(True, self.browser.is_text_present('Attribute'))
        assert_equals(True, self.browser.is_text_present('Value'))


class GroupsListingPage(PageObject):
    url = '/groups/'

    def validate_fields(self):
        assert_equals(True, self.browser.is_text_present('Groups List'))
        assert_equals(True, self.browser.is_text_present('Order'))
        assert_equals(True, self.browser.is_text_present('Group name'))
        assert_equals(True, self.browser.is_text_present('Actions'))


class AddConditionPage(PageObject):
    url = "/conditions/new/"


class AddGroupPage(PageObject):
    url = '/groups/new/'


class GroupConditionModalPage(PageObject):
    url = ''

    def validate_contents(self):
        assert_equals(True, self.browser.is_text_present('New Condition'))
        assert_equals(True, self.browser.is_text_present('Condition'))
        assert_equals(True, self.browser.is_text_present('Attribute'))
        assert_equals(True, self.browser.is_text_present('Value'))

    def click_button(self,name):
        self.browser.find_by_name(name).click()

    def validate_latest_condition(self, condition):
        self.browser.find_by_value("%s > %s > %s" % (condition.attribute, condition.condition, condition.value))
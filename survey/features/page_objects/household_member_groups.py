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
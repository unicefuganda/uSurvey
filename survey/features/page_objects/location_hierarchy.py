from survey.features.page_objects.base import PageObject
from nose.tools import assert_equals


class AddLocationHierarchyPage(PageObject):
    def __init__(self, browser):
        super(AddLocationHierarchyPage, self).__init__(browser)
        self.url = '/locations/hierarchy/add/'

    def see_field_details(self, level, form, status=True):
        assert_equals(status, self.browser.is_text_present(level))
        status = 1 if status else 0
        for field in ['levels', 'required', 'has_code', 'code']:
            assert_equals(status, len(self.browser.find_by_name(form + '-levels')))

    def submit(self):
        self.browser.find_by_name('save_button').first.click()
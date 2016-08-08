# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from survey.features.page_objects.base import PageObject


class UploadLocationsPage(PageObject):
    def __init__(self, browser):
        super(UploadLocationsPage, self).__init__(browser)
        self.url = '/locations/upload/'

    def validate_typecode_appear_before_typename(self, type_name, length_of_code):
        headers = self.browser.find_by_css('th')
        assert headers[0].value == type_name.capitalize()+'Code'
        assert headers[1].value == type_name.capitalize()+'Name'

        self.is_text_present('0'*length_of_code )


class UploadBase(PageObject):
    def submit(self):
        self.browser.find_by_name('save_button').first.click()

    def validate_layout_collapsed(self):
        collapse_element = self.browser.find_by_css("#collapse_table")
        assert not 'in' in collapse_element.first['class']


class UploadWeightsPage(UploadBase):
    def __init__(self, browser):
        super(UploadWeightsPage, self).__init__(browser)
        self.url = '/locations/weights/upload/'


class UploadEAPage(UploadBase):
    def __init__(self, browser):
        super(UploadEAPage, self).__init__(browser)
        self.url = '/locations/enumeration_area/upload/'

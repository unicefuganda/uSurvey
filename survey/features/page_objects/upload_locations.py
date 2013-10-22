# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from survey.features.page_objects.base import PageObject


class UploadLocationsPage(PageObject):
    def __init__(self, browser):
        super(UploadLocationsPage, self).__init__(browser)
        self.url = '/locations/upload/'
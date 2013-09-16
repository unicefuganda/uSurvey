from survey.features.page_objects.base import PageObject
from nose.tools import assert_equals


class SurveyListPage(PageObject):
    url = '/surveys/'

    def validate_fields(self):
        self.validate_fields_present(["Survey List", "Name", "Description", "Type", "Sample Size", "Actions"])

class AddSurveyPage(PageObject):
    url = '/surveys/new/'
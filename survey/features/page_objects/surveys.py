from survey.features.page_objects.base import PageObject

class SurveyListPage(PageObject):
    url = '/surveys/'

    def validate_fields(self):
        self.validate_fields_present(["Survey List", "Name", "Description", "Type", "Number of Households per Investigator", "Actions"])

class AddSurveyPage(PageObject):
    url = '/surveys/new/'
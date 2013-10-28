from survey.features.page_objects.base import PageObject


class SurveyCompletionRatesPage(PageObject):
    def __init__(self, browser):
        super(SurveyCompletionRatesPage, self).__init__(browser)
        self.url = '/survey_completion/'
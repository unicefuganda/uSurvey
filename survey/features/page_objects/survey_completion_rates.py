from rapidsms.contrib.locations.models import Location
from survey.features.page_objects.base import PageObject


class SurveyCompletionRatesPage(PageObject):
    def __init__(self, browser):
        super(SurveyCompletionRatesPage, self).__init__(browser)
        self.url = '/survey_completion/'

    def choose_location(self, locations):
        for key, value in locations.items():
            object_id = "location-%s" % key
            assert self.browser.is_element_present_by_id(object_id)
            jquery_id = '$("#%s")' % object_id
            location = Location.objects.get(name=value)
            self.fill_in_with_js(jquery_id, location.pk)

    def check_if_batches_present(self, *batches):
        all_options = self.browser.find_by_id('batch-list-select')[0].find_by_tag('option')
        all_options = [option.text for option in all_options]
        for batch in batches:
            assert batch.name in all_options

    def check_get_status_button_presence(self):
        assert self.browser.find_by_css("#aggregates-form")[0].find_by_tag('button')[0].text == "Get status"

    def choose_batch(self, batch):
        self.browser.select('batch', batch.pk)

    def see_completion_rates_table(self):
        assert self.browser.is_text_present('Location')
        assert self.browser.is_text_present('Total Household')
        assert self.browser.is_text_present('% Completed')

    def see_houdehold_completion_table(self):
        assert self.browser.is_text_present('HH Code')
        assert self.browser.is_text_present('Household Head')
        assert self.browser.is_text_present('Number of members')
        assert self.browser.is_text_present('Total Interviewed')


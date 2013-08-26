# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from rapidsms.contrib.locations.models import Location
from survey.features.page_objects.base import PageObject


class AggregateStatusPage(PageObject):
    url = "/aggregates/status"

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

    def assert_status_count(self, pending_households, completed_housesholds, pending_clusters, completed_clusters):
        assert self.browser.find_by_id('pending-households-count')[0].text == str(pending_households)
        assert self.browser.find_by_id('completed-households-count')[0].text == str(completed_housesholds)
        assert self.browser.find_by_id('pending-clusters-count')[0].text == str(pending_clusters)
        assert self.browser.find_by_id('completed-clusters-count')[0].text == str(completed_clusters)

    def check_presence_of_investigators(self, *investigators):
        for investigator in investigators:
            self.is_text_present(investigator.name)
            self.is_text_present(investigator.mobile_number)
            self.is_text_present("10")

    def assert_presence_of_batch_is_closed_message(self):
        self.is_text_present("This batch is currently closed for this location.")

    def select_all_district(self):
        self.browser.execute_script(
            "$('#location-district').val('').change().trigger('liszt:updated').chosen().change();")

    def see_all_districts_location_selected(self):
        assert self.browser.find_by_css('input[name=location]')[0].value == ''


class DownloadExcelPage(PageObject):
    url = "/aggregates/download_spreadsheet"

    def export_to_csv(self, batch):
        self.browser.select('batch', batch.pk)
        # self.submit()
from rapidsms.contrib.locations.models import Location
from survey.features.page_objects.base import PageObject

class NewLocationTypePage(PageObject):
    url = "/locations/type/new/"

    def validate_location_type_fields(self):
        assert self.browser.is_element_present_by_name('name')

class NewLocationPage(PageObject):
    url = "/locations/new/"

# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from survey.features.page_objects.base import PageObject
from survey.investigator_configs import COUNTRY_PHONE_CODE
from rapidsms.contrib.locations.models import Location
from lettuce.django import django_url
from survey.models import EnumerationArea


class NewInvestigatorPage(PageObject):
    url = "/investigators/new/"

    def valid_page(self):
        fields = ['name', 'mobile_number',
                  'confirm_mobile_number', 'male', 'age', 'backend']
        for field in fields:
            assert self.browser.is_element_present_by_name(field)
        assert self.browser.find_by_css(
            "span.add-on")[0].text == COUNTRY_PHONE_CODE

    def get_investigator_values(self):
        return self.values

    def validate_detail_page_url(self):
        assert self.browser.url == django_url(self.url)

    def fill_valid_values(self, values, ea):
        self.browser.find_by_id(
            "location-value").value = Location.objects.create(name="Uganda").id
        kampala = Location.objects.get(name="Kampala")
        kampala_county = Location.objects.get(name="Kampala County")
        kampala_subcounty = Location.objects.get(name="Subcounty")
        kampala_parish = Location.objects.get(name="Parish")
        kampala_village = Location.objects.get(name="Village")
        ea = EnumerationArea.objects.get(name="EA")
        self.fill_in_with_js('$("#location-district")', kampala.id)
        self.fill_in_with_js('$("#location-county")', kampala_county.id)
        self.fill_in_with_js('$("#location-subcounty")', kampala_subcounty.id)
        self.fill_in_with_js('$("#location-parish")', kampala_parish.id)
        self.fill_in_with_js('$("#location-village")', kampala_village.id)
        self.fill_in_with_js('$("#widget_ea")', ea.id)

        self.values = values
        self.browser.fill_form(self.values)


class InvestigatorsListPage(PageObject):
    url = '/investigators/'

    def validate_fields(self):
        self.validate_fields_present(
            ["Investigators List", "Name", "Mobile Number", "Action"])

    def validate_pagination(self):
        self.browser.click_link_by_text("2")

    def validate_presence_of_investigator(self, values):
        assert self.browser.is_text_present(values['name'])
        assert self.browser.is_text_present(values['mobile_number'])

    def no_registered_invesitgators(self):
        assert self.browser.is_text_present(
            "There are no investigators currently registered for this location.")

    def visit_investigator(self, investigator):
        self.browser.click_link_by_text(investigator.name)

    def see_confirm_block_message(self, confirmation_type, investigator):
        self.is_text_present("Confirm: Are you sure you want to %s investigator %s" % (
            confirmation_type, investigator.name))

    def validate_successful_edited_message(self):
        self.is_text_present("Investigator successfully edited.")

    def validate_page_url(self):
        assert self.browser.url == django_url(self.url)


class FilteredInvestigatorsListPage(InvestigatorsListPage):

    def __init__(self, browser, location_id):
        self.browser = browser
        self.url = '/investigators/?location=' + str(location_id)

    def no_registered_invesitgators(self):
        assert self.browser.is_text_present(
            "There are no investigators currently registered for this county.")


class EditInvestigatorPage(PageObject):

    def __init__(self, browser, investigator):
        self.browser = browser
        self.investigator = investigator
        self.url = '/investigators/' + str(investigator.id) + '/edit/'

    def validate_edit_investigator_url(self):
        assert self.browser.url == django_url(self.url)

    def change_name_of_investigator(self):
        self.values = {
            'name': 'Updated Name',
            'mobile_number': self.investigator.mobile_number,
            'confirm_mobile_number': self.investigator.mobile_number,
            'male': self.investigator.male,
            'age': self.investigator.age,
            'level_of_education': self.investigator.level_of_education,
            'language': self.investigator.language,
            'location': self.investigator.location,
        }
        self.browser.fill_form(self.values)

    def assert_user_saved_sucessfully(self):
        self.is_text_present("User successfully edited.")


class InvestigatorDetailsPage(PageObject):

    def __init__(self, browser, investigator):
        self.browser = browser
        self.investigator = investigator
        self.url = '/investigators/' + str(investigator.id) + '/'

    def validate_page_content(self):
        details = {
            'Name': self.investigator.name,
            'Mobile Number': self.investigator.mobile_number,
            'Age': str(self.investigator.age),
            'Sex': 'Male' if self.investigator.male else 'Female',
            'Highest Level of Education': self.investigator.level_of_education,
            'Preferred Language of Communication': self.investigator.language,
            'Country': 'Uganda',
            'City': 'Kampala',
        }
        for label, text in details.items():
            self.is_text_present(label)
            self.is_text_present(text)

    def validate_navigation_links(self):
        assert self.browser.find_link_by_text(' Back')

    def validate_back_link(self):
        self.browser.find_link_by_href(django_url(InvestigatorsListPage.url))

    def validate_detail_page_url(self):
        assert self.browser.url == django_url(self.url)

    def validate_successful_edited_message(self):
        self.is_text_present("Investigator successfully edited.")

# -*- coding: utf-8 -*-
from lettuce.django import django_url
from random import randint
from time import sleep
from rapidsms.contrib.locations.models import Location
from survey.models import Investigator
from survey.investigator_configs import *
from rapidsms.contrib.locations.models import *

class PageObject(object):
    def __init__(self, browser):
        self.browser = browser

    def visit(self):
        self.browser.visit(django_url(self.url))

    def random_text(self, text):
        return text +  str(randint(1, 999))

    def fill(self, name, value):
        self.browser.fill(name, value)

    def is_text_present(self, text):
        assert self.browser.is_text_present(text)

    def is_disabled(self, element_id):
        try:
            self.browser.find_by_css('#%s[disabled=disabled]' % element_id).first
            return True
        except Exception, e:
            return False

    def fill_in_with_js(self, jquery_id, object_id):
        script = '%s.val(%s).change(); %s.trigger("liszt:updated").chosen().change()' % (jquery_id, object_id, jquery_id)
        self.browser.execute_script(script)
        sleep(2)

    def submit(self):
        self.browser.find_by_css("form button").first.click()

    def see_logout_link(self):
        assert self.browser.find_link_by_text('logout')

class NewInvestigatorPage(PageObject):
    url = "/investigators/new"

    def valid_page(self):
        fields = ['name', 'mobile_number', 'confirm_mobile_number', 'male', 'age']
        fields += [location_type.name.lower() for location_type in LocationType.objects.all()]
        for field in fields:
            assert self.browser.is_element_present_by_name(field)
        assert self.browser.find_by_css("span.add-on")[0].text == COUNTRY_PHONE_CODE

    def get_investigator_values(self):
        return self.values

    def fill_valid_values(self):
        self.browser.find_by_id("location-value").value = Location.objects.create(name="Uganda").id
        self.values = {
            'name': self.random_text('Investigator Name'),
            'mobile_number': "987654321",
            'confirm_mobile_number': "987654321",
            'male': 't',
            'age': '25',
            'level_of_education': 'Primary',
            'language': 'Luo',
      }
        self.browser.fill_form(self.values)
        kampala = Location.objects.get(name="Kampala")
        kampala_county = Location.objects.get(name="Kampala County")
        script = '$("#investigator-district").val(%s);$("#investigator-district").trigger("liszt:updated").chosen().change()' % kampala.id
        self.browser.execute_script(script)
        sleep(3)
        script = '$("#investigator-county").val(%s);$("#investigator-county").trigger("liszt:updated").chosen().change()' % kampala_county.id
        self.browser.execute_script(script)

    def submit(self):
        sleep(2)
        self.browser.find_by_css("form button").first.click()

class InvestigatorsListPage(PageObject):
    url = '/investigators/'

    def validate_fields(self):
        assert self.browser.is_text_present('Investigators List')
        assert self.browser.is_text_present('Name')
        assert self.browser.is_text_present('Mobile Number')
        assert self.browser.is_text_present('Action')

    def validate_pagination(self):
        self.browser.click_link_by_text("2")

    def validate_presence_of_investigator(self, values):
        assert self.browser.is_text_present(values['name'])
        assert self.browser.is_text_present(values['mobile_number'])

    def no_registered_invesitgators(self):
        assert self.browser.is_text_present("There are no investigators currently registered for this location.")

class FilteredInvestigatorsListPage(InvestigatorsListPage):
    def __init__(self, browser, location_id):
        self.browser = browser
        self.url = '/investigators/?location=' + str(location_id)

    def no_registered_invesitgators(self):
        assert self.browser.is_text_present("There are no investigators currently registered for this county.")

class NewHouseholdPage(PageObject):
    url = "/households/new"

    def valid_page(self):
        fields = ['investigator', 'surname', 'first_name', 'male', 'age', 'occupation',
                   'level_of_education', 'resident_since_month', 'resident_since_year']
        fields += ['number_of_males', 'number_of_females', 'size']
        fields += ['has_children', 'has_children_below_5','aged_between_5_12_years', 'aged_between_13_17_years', 'aged_between_0_5_months',
                    'aged_between_6_11_months', 'aged_between_12_23_months', 'aged_between_24_59_months']
        fields += ['has_women','aged_between_15_19_years', 'aged_between_20_49_years']
        fields += [location_type.name.lower() for location_type in LocationType.objects.all()]
        for field in fields:
            assert self.browser.is_element_present_by_name(field)

    def get_investigator_values(self):
        return self.values

    def fill_valid_values(self):
        self.browser.find_by_id("location-value").value = Location.objects.create(name="Uganda").id
        self.values = {
            'surname': self.random_text('house'),
            'first_name': self.random_text('ayoyo'),
            'age': '25',
      }
        self.browser.fill_form(self.values)
        kampala = Location.objects.get(name="Kampala")
        kampala_county = Location.objects.get(name="Kampala County")
        investigator = Investigator.objects.get(name="Investigator name")
        self.fill_in_with_js('$("#investigator-district")', kampala.id)
        self.fill_in_with_js('$("#investigator-county")', kampala_county.id)
        self.fill_in_with_js('$("#household-investigator")', investigator.id)
        self.fill_in_with_js('$("#household-extra_resident_since_year")', 1984)
        self.fill_in_with_js('$("#household-extra_resident_since_month")', 1)

    def validate_household_created(self):
        assert self.browser.is_text_present("Household successfully registered.")

    def has_children(self, value):
        self.browser.choose('has_children', value)

    def are_children_fields_disabled(self, is_disabled = True):
        for element_id in ['aged_between_5_12_years', 'aged_between_13_17_years']:
            element_id = 'household-children-' + element_id
            assert self.is_disabled(element_id) == is_disabled
        self.are_children_below_5_fields_disabled(is_disabled=is_disabled)

    def is_no_below_5_checked(self):
        assert self.browser.find_by_id('household-children-has_children_below_5_1').selected == True

    def cannot_say_yes_to_below_5(self):
        self.browser.choose('has_children_below_5', 'True')
        self.are_children_fields_disabled()

    def has_children_below_5(self, value):
        self.browser.choose('has_children_below_5', value)

    def are_children_below_5_fields_disabled(self, is_disabled = True):
        for element_id in ['aged_between_0_5_months','aged_between_6_11_months', 'aged_between_12_23_months', 'aged_between_24_59_months']:
            element_id = 'household-children-' + element_id
            assert self.is_disabled(element_id) == is_disabled

    def has_women(self, value):
        self.browser.choose('has_women', value)

    def are_women_fields_disabled(self, is_disabled=True):
        for element_id in ['aged_between_15_19_years', 'aged_between_20_49_years']:
            element_id = 'household-women-' + element_id
            assert self.is_disabled(element_id) == is_disabled

    def fill_in_number_of_females_lower_than_sum_of_15_19_and_20_49(self):
        self.browser.fill('number_of_females', '1')
        self.browser.fill('aged_between_15_19_years', '2')
        self.browser.fill('aged_between_20_49_years', '3')

    def see_an_error_on_number_of_females(self):
        self.is_text_present('Please enter a value that is greater or equal to the total number of women above 15 years age.')

class AggregateStatusPage(PageObject):
    url = "/aggregates/status"

    def choose_location(self, locations):
        for key, value in locations.items():
            object_id = "location-%s" % key
            assert self.browser.is_element_present_by_id(object_id)
            jquery_id = '$("#%s")' % object_id
            location = Location.objects.get(name = value)
            self.fill_in_with_js(jquery_id, location.pk)

    def check_if_batches_present(self, *batches):
        all_options = self.browser.find_by_id('batch-list-select')[0].find_by_tag('option')
        all_options = [ option.text for option in all_options ]
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
        self.browser.execute_script("$('#location-district').val('').change().trigger('liszt:updated').chosen().change();")

    def see_all_districts_location_selected(self):
        assert self.browser.find_by_css('input[name=location]')[0].value == ''

class DownloadExcelPage(PageObject):
    url = "/aggregates/download_spreadsheet"

    def export_to_csv(self, batch):
        self.browser.select('batch', batch.pk)
        self.submit()

class LoginPage(PageObject):
    url = "/accounts/login"

    def login(self, user):
        self.is_text_present('Type your username and password')

        user.set_password('secret')
        user.save()
        details={'username': user.username,
                 'password': 'secret',
        }

        self.browser.fill_form(details)
        self.submit()

    def see_home_page_and_logout_link(self):
        assert self.browser.find_by_css('title').first.text == 'Home | mMICS'
        assert self.url not in self.browser.url
        self.see_logout_link()

class HomePage(PageObject):
    url = "/"

    def click_the_login_link(self):
        self.browser.click_link_by_text('login')

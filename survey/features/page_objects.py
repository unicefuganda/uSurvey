# -*- coding: utf-8 -*-
from lettuce.django import django_url
from random import randint
from time import sleep
from rapidsms.contrib.locations.models import Location
from survey.models import Investigator
from investigator_configs import *
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
        assert self.browser.is_text_present("There are no investigators registered.")

class FilteredInvestigatorsListPage(InvestigatorsListPage):
    def __init__(self, browser, location_id):
        self.browser = browser
        self.url = '/investigators/filter/' + str(location_id)

    def no_registered_invesitgators(self):
        assert self.browser.is_text_present("There are no investigators registered for this county.")

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

    def fill_in_with_js(self, jquery_id, object_id):
        script = '%s.val(%s); %s.trigger("liszt:updated").chosen().change()' % (jquery_id, object_id, jquery_id)
        self.browser.execute_script(script)
        sleep(2)

    def submit(self):
        sleep(2)
        self.browser.find_by_css("form button").first.click()

    def validate_household_created(self):
        assert self.browser.is_text_present("Household successfully registered.")



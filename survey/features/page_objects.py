# -*- coding: utf-8 -*-
from lettuce.django import django_url
from random import randint
from time import sleep
from rapidsms.contrib.locations.models import Location
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
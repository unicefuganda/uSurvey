# -*- coding: utf-8 -*-
from lettuce.django import django_url
from random import randint
from time import sleep
from rapidsms.contrib.locations.models import Location

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

    def get_investigator_values(self):
        return self.values

    def fill_valid_values(self):
        self.browser.find_by_id("location-value").value = Location.objects.create(name="Uganda").id
        self.values = {
            'name': self.random_text('Investigator Name'),
            'mobile_number': "9876543210",
            'male': 't',
            'age': '25',
            'level_of_education': 'Primary',
            'language': 'Luo',
            'location-name': 'Uganda',
        }
        self.browser.fill_form(self.values)
        self.browser.find_by_css("ul.typeahead a").first.click()

    def submit(self):
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
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

class NewInvestigatorPage(PageObject):
    url = "/investigators/new"

    def fill_valid_values(self):
        self.browser.fill_form({
            'name': self.random_text('Investigator Name'),
            'mobile_number': "9876543210",
            'male': 't',
            'age': '25',
            'level_of_education': 'Primary',
            'language': 'Luo',
            'location-name': 'Uganda',
            'location': Location.objects.create(name="Uganda").id,
        })

    def submit(self):
        self.browser.find_by_css("form button").first.click()
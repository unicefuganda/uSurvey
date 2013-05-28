# -*- coding: utf-8 -*-
from lettuce import *
from page_objects import *
from random import randint
from survey.models import *
from rapidsms.contrib.locations.models import Location

@step(u'Given I am logged in as researcher')
def given_i_am_logged_in_as_researcher(step):
    assert True

@step(u'And I visit new investigator page')
def and_i_visit_new_investigator_page(step):
    world.page = NewInvestigatorPage(world.browser)
    world.page.visit()

@step(u'And I fill all necessary fields')
def and_i_fill_all_necessary_fields(step):
    world.page.fill_valid_values()

@step(u'And I submit the form')
def and_i_submit_the_form(step):
    world.page.submit()

@step(u'Then I should see that the investigator is created')
def then_i_should_see_that_the_investigator_is_created(step):
    index_page = InvestigatorsListPage(world.browser)
    index_page.visit()
    index_page.validate_presence_of_investigator( world.page.get_investigator_values() )

@step(u'Given I have 100 investigators')
def given_i_have_100_investigators(step):
    uganda = Location.objects.create(name="Uganda")
    for _ in xrange(100):
        random_number = str(randint(1, 99999))
        Investigator.objects.create(name="Investigator " + random_number, mobile_number = random_number, age = 12, level_of_education = "Nursery", language = "Luganda", location = uganda)

@step(u'And I visit investigators listing page')
def and_i_visit_investigators_listing_page(step):
    world.page = InvestigatorsListPage(world.browser)
    world.page.visit()

@step(u'And I should see the investigators list paginated')
def and_i_should_see_the_investigators_list_paginated(step):
    world.page.validate_fields()
    world.page.validate_pagination()
    world.page.validate_fields()
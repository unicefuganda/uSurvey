# -*- coding: utf-8 -*-
from lettuce import *
from page_objects import *
from random import randint
from survey.models import *
from rapidsms.contrib.locations.models import *
from django.template.defaultfilters import slugify

@step(u'And I visit new household page')
def and_i_visit_new_household_page(step):
    world.page = NewHouseholdPage(world.browser)
    world.page.visit()

@step(u'And I see all households fields are present')
def and_i_see_all_households_fields_are_present(step):
    world.page.valid_page()

@step(u'And I have an investigator in that location')
def and_i_have_an_investigator_in_that_location(step):
    kampala_county = Location.objects.get(name="Kampala County")
    investigator = Investigator.objects.create(name="Investigator name", location=kampala_county)

@step(u'Then I should see that the household is created')
def then_i_should_see_that_the_household_is_created(step):
    world.page.validate_household_created()
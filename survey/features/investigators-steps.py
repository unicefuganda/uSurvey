# -*- coding: utf-8 -*-
from lettuce import *
from page_objects import *
from random import randint
from survey.models import *
from rapidsms.contrib.locations.models import *
from django.template.defaultfilters import slugify

@step(u'Given I am logged in as researcher')
def given_i_am_logged_in_as_researcher(step):
    user = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
    world.page = LoginPage(world.browser)
    world.page.visit()
    world.page.login(user)

@step(u'And I have locations')
def and_i_have_locations(step):
    district = LocationType.objects.create(name="district", slug=slugify("district"))
    county = LocationType.objects.create(name="county", slug=slugify("county"))

    kampala = Location.objects.create(name="Kampala", type=district)
    kampala_county = Location.objects.create(name="Kampala County", type=county, tree_parent=kampala)


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
        try:
            Investigator.objects.create(name="Investigator " + random_number, mobile_number = random_number, age = 12, level_of_education = "Nursery", language = "Luganda", location = uganda)
        except Exception:
            pass

@step(u'And I visit investigators listing page')
def and_i_visit_investigators_listing_page(step):
    world.page = InvestigatorsListPage(world.browser)
    world.page.visit()

@step(u'And I should see the investigators list paginated')
def and_i_should_see_the_investigators_list_paginated(step):
    world.page.validate_fields()
    world.page.validate_pagination()
    world.page.validate_fields()

@step(u'And I fill in already registered mobile number')
def and_i_fill_in_already_registered_mobile_number(step):
    world.investigator = Investigator.objects.create(name="investigator", mobile_number="987654321")
    world.page.fill("mobile_number", world.investigator.mobile_number)

@step(u'Then I should see that mobile number is already taken')
def then_i_should_see_that_mobile_number_is_already_taken(step):
    world.page.is_text_present(world.investigator.mobile_number + " is already registered.")

@step(u'And I see all the fields are present')
def and_i_see_all_the_fields_are_present(step):
    world.page.valid_page()

@step(u'Then I should see the error messages')
def then_i_should_see_the_error_messages(step):
    world.page.is_text_present("This field is required.")

@step(u'Given I have no investigators')
def given_i_have_no_investigators(step):
    Investigator.objects.all().delete()

@step(u'And I should see no investigators registered message')
def and_i_should_see_no_investigators_registered_message(step):
    world.page.no_registered_invesitgators()

@step(u'And I request filter list of a County with no associated investigator')
def and_i_request_filter_list_for_another_county_with_no_investigator(step):
    county_type = LocationType.objects.get(name='county')
    new_county = Location.objects.create(name="some county", type=county_type)
    Investigator.objects.filter(location=new_county).delete()
    world.page = FilteredInvestigatorsListPage(world.browser, new_county.id)
    world.page.visit()

@step(u'Then I should see no investigator for this County')
def then_i_should_see_no_investigator_for_this_county(step):
    world.page.no_registered_invesitgators()


#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
from random import randint

from django.template.defaultfilters import slugify
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from lettuce import *
from survey.features.page_objects.accounts import LoginPage
from survey.features.page_objects.investigators import NewInvestigatorPage, InvestigatorsListPage, FilteredInvestigatorsListPage, EditInvestigatorPage, InvestigatorDetailsPage
from survey.models_file import *
from rapidsms.contrib.locations.models import *


def set_permissions(group, permissions_codename_list):
    auth_content = ContentType.objects.get_for_model(Permission)
    for codename in permissions_codename_list:
        permission, out = Permission.objects.get_or_create(codename=codename, content_type=auth_content)
        group.permissions.add(permission)

def create_reacher():
    researcher = Group.objects.create(name='researcher1')
    user = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
    researcher.user_set.add(user)
    set_permissions(researcher, ['can_view_aggregates', 'can_view_households', 'can_view_batches', 'can_view_investigators'])

    return user

@step(u'Given I am logged in as researcher')
def given_i_am_logged_in_as_researcher(step):
    user = create_reacher()
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

@step(u'And I have one investigator')
def and_i_have_an_investigator(step):
    country = LocationType.objects.create(name="Country", slug=slugify("country"))
    city = LocationType.objects.create(name="City", slug=slugify("city"))
    uganda = Location.objects.create(name="Uganda", type=country)
    kampala = Location.objects.create(name="Kampala", type=city, tree_parent=uganda)
    world.investigator = Investigator.objects.create(name="Rajni", mobile_number = "123456789", age = 25, level_of_education = "Nursery", language = "Luganda", location = kampala)

@step(u'And I visit investigators page')
def and_i_visit_investigators_page(step):
    world.page = InvestigatorsListPage(world.browser)
    world.page.visit()

@step(u'And I click on the investigators name')
def and_i_click_on_the_investigators_name(step):
    world.page.visit_investigator(world.investigator)

@step(u'Then I should see his details displayed')
def then_i_should_see_his_details_displayed(step):
    world.page = InvestigatorDetailsPage(world.browser, world.investigator)
    world.page.validate_page_content()

@step(u'And I should see navigation links')
def and_i_should_see_navigation_links(step):
    world.page.validate_navigation_links()

@step(u'Then back button should take back to Investigator Listing page')
def then_back_button_should_take_back_to_investigator_listing_page(step):
    world.page.validate_back_link()

@step(u'And I click on the edit button')
def and_i_click_on_the_edit_button(step):
    world.page.click_actions_button()
    world.page.click_link_by_text(" Edit")

@step(u'Then it should be able to take me to edit form page')
def then_it_should_be_able_to_take_me_to_edit_form_page(step):
    world.page = EditInvestigatorPage(world.browser, world.investigator)
    world.page.validate_edit_investigator_url()
    world.page.visit()

@step(u'And I change Name of investigator')
def and_i_change_name_of_investigator(step):
    world.page.change_name_of_investigator()

@step(u'And I click on save')
def and_i_click_on_save(step):
    world.page.submit()

@step(u'Then I should go back to investigator details page')
def then_i_should_go_back_to_investigator_details_page(step):
    world.page = InvestigatorDetailsPage(world.browser, world.investigator)
    world.page.validate_detail_page_url()

@step(u'And I should see name of investigator updated')
def and_i_should_see_name_of_investigator_updated(step):
    world.page.validate_successful_edited_message()

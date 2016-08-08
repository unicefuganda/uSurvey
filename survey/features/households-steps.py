# -*- coding: utf-8 -*-
from random import randint
from datetime import date
from time import sleep

from lettuce import *

from rapidsms.contrib.locations.models import *
from django.template.defaultfilters import slugify

from survey.features.page_objects.households import NewHouseholdPage, HouseholdsListPage, HouseholdDetailsPage, EditHouseholdsPage
from survey.models import EnumerationArea
from survey.models.households import HouseholdMember, HouseholdHead, Household
from survey.models.investigator import Investigator


def random_text(text):
    return text + str(randint(1, 999))


@step(u'And I visit new household page')
def and_i_visit_new_household_page(step):
    world.page = NewHouseholdPage(world.browser)
    world.page.visit()

@step(u'And I fill household data')
def and_i_fill_household_data(step):
    values = {
        'surname': random_text('house'),
        'first_name': random_text('ayoyo'),
        'date_of_birth': '1980-02-01',
        'uid': '2'}
    world.page.fill_valid_values(values, world.ea)

@step(u'And I see all households fields are present')
def and_i_see_all_households_fields_are_present(step):
    world.page.valid_page()

@step(u'And I have an investigator in that location')
def and_i_have_an_investigator_in_that_location(step):
    world.investigator = Investigator.objects.create(name="Investigator name", ea=world.ea)

@step(u'Then I should see that the household is created')
def then_i_should_see_that_the_household_is_created(step):
    world.household_uid = world.page.get_household_values()['uid']
    world.page.validate_household_created()

@step(u'And I click No to has children')
def and_i_click_no_to_has_children(step):
    world.page.has_children('False')

@step(u'Then I should see children number fields disabled')
def then_i_should_see_children_number_fields_disabled(step):
    world.page.are_children_fields_disabled()

@step(u'And No below 5 is also checked')
def and_no_below_5_is_also_checked(step):
    world.page.is_no_below_5_checked()

@step(u'And checking below 5 to yes does not work')
def and_checking_below_5_to_yes_does_not_work(step):
    world.page.cannot_say_yes_to_below_5()

@step(u'And Now If I click to Yes to has children')
def and_now_if_i_click_to_yes_to_has_children(step):
    world.page.has_children('True')

@step(u'Then all children number fields are enabled back')
def then_all_children_number_fields_are_enabled_back(step):
    world.page.are_children_fields_disabled(is_disabled = False)

@step(u'And I click No to has below 5')
def and_i_click_no_to_has_below_5(step):
    world.page.has_children_below_5('False')

@step(u'Then I should see below 5 number fields disabled')
def then_i_should_see_below_5_number_fields_disabled(step):
    world.page.are_children_below_5_fields_disabled(is_disabled=True)

@step(u'And Now If I click Yes to below 5')
def and_now_if_i_click_yes_to_below_5(step):
    world.page.has_children_below_5('True')

@step(u'Then below 5 number fields are enabled back')
def then_below_5_number_fields_are_enabled_back(step):
    world.page.are_children_below_5_fields_disabled(is_disabled=False)

@step(u'And I click No to has women')
def and_i_click_no_to_has_women(step):
    world.page.has_women('False')

@step(u'Then I should see has women number fields disabled')
def then_i_should_see_has_women_number_fields_disabled(step):
    world.page.are_women_fields_disabled()

@step(u'And Now If I click Yes to has women')
def and_now_if_i_click_yes_to_has_women(step):
    world.page.has_women('True')

@step(u'Then has women number fields are enabled back')
def then_has_women_number_fields_are_enabled_back(step):
    world.page.are_women_fields_disabled(is_disabled=False)

@step(u'And I fill in number_of_females lower than sum of 15_19 and 20_49')
def and_i_fill_in_number_of_females_lower_than_sum_of_15_19_and_20_49(step):
    world.page.fill_in_number_of_females_lower_than_sum_of_15_19_and_20_49()

@step(u'Then I should see an error on number_of_females')
def then_i_should_see_an_error_on_number_of_females(step):
    world.page.see_an_error_on_number_of_females()

@step(u'And Now If I choose Other as occupation')
def and_now_if_i_choose_other_as_occupation(step):
    world.page.choose_occupation('Other: ')

@step(u'Then I have to specify one')
def then_i_have_to_specify_one(step):
    world.page.is_specify_visible(True)

@step(u'And If I choose a different occupation')
def and_if_i_choose_a_different_occupation(step):
    world.page.choose_occupation('Business person')

@step(u'Then Specify disappears')
def then_specify_disappears(step):
    world.page.is_specify_visible(False)

@step(u'Given I have an investigator')
def given_i_have_an_investigator(step):
    country = LocationType.objects.create(name="Country", slug=slugify("country"))
    uganda = Location.objects.create(name="Uganda", type=country)
    world.ea = EnumerationArea.objects.create(name="EA")
    world.ea.locations.add(uganda)

    world.investigator = Investigator.objects.create(name="Investigator ", mobile_number='987654321', age=20,
                                                     level_of_education="Nursery", language="Luganda", ea=world.ea)

@step(u'Given I have 100 households')
def given_i_have_100_households(step):
    for i in xrange(100):
        random_number = str(randint(1, 99999))
        try:
            HouseholdHead.objects.create(surname="head" + random_number, date_of_birth='1980-06-01', male=False, household=Household.objects.create(investigator=world.investigator, location=world.investigator.location, uid=i, ea=world.investigator.ea))
        except Exception:
            pass

@step(u'And I visit households listing page')
def and_i_visit_households_listing_page(step):
    world.page = HouseholdsListPage(world.browser)
    world.page.visit()

@step(u'And I should see the households list paginated')
def and_i_should_see_the_households_list_paginated(step):
    world.page.validate_fields()
    world.page.validate_pagination()

@step(u'Given I have no households')
def given_i_have_no_households(step):
    Household.objects.all().delete()

@step(u'And I should see no household message')
def and_i_should_see_no_household_message(step):
    world.page.no_registered_huseholds()

@step(u'And I select list households')
def and_i_select_list_households(step):
    world.page.click_link_by_text("Households")
    world.page = HouseholdsListPage(world.browser)

@step(u'When I click add household button')
def when_i_click_add_household_button(step):
    world.page = HouseholdsListPage(world.browser)
    world.page.visit()
    world.page.click_by_css("#add-household")

@step(u'Then I should see add household page')
def then_i_should_see_add_household_page(step):
    world.page = NewHouseholdPage(world.browser)
    world.page.validate_url()

@step(u'And then I click on that household ID')
def and_when_i_click_on_that_household_id(step):
    world.page.click_link_by_text(world.household.uid)

@step(u'And I should see that household details, its head and members')
def and_i_should_see_that_household_details_its_head_and_members(step):
    world.page.validate_household_details()
    world.page.validate_household_member_details()

@step(u'And I have a member for that household')
def and_i_have_a_member_for_that_household(step):
    world.household = Household.objects.get(uid=world.household_uid)
    fields_data = dict(surname='xyz', male=True, date_of_birth=date(1980, 05, 01), household=world.household)
    HouseholdMember.objects.create(**fields_data)

@step(u'Then I should see household member title and add household member link')
def then_i_should_see_household_member_title_and_add_household_member_link(step):
    world.page = HouseholdDetailsPage(world.browser, world.household)
    world.page.validate_household_member_title_and_add_household_member_link()

@step(u'And I should see actions edit and delete member')
def and_i_should_see_actions_edit_and_delete_member(step):
    world.page.validate_actions_edit_and_delete_member()

@step(u'And I have two other investigators')
def and_i_have_two_other_investigators(step):
    world.investigator_1 = Investigator.objects.create(name="Investigator name", ea=world.ea, mobile_number="123456789")
    world.investigator_2 = Investigator.objects.create(name="Investigator name", ea=world.ea, mobile_number="123456782")

@step(u'And I click on that household ID')
def and_i_click_on_that_household_id(step):
    world.page.click_link_by_text(world.household.uid)

@step(u'Then I should be on the household details page')
def then_i_should_be_on_the_household_details_page(step):
    world.page = HouseholdDetailsPage(world.browser, world.household)
    world.page.validate_url()

@step(u'When I click edit household')
def when_i_click_edit_household(step):
    world.browser.find_link_by_text(' Edit Household').first.click()

@step(u'Then I should see edit household form')
def then_i_should_see_edit_household_form(step):
    world.page = EditHouseholdsPage(world.browser, world.household)
    world.related_location = world.household.get_related_location()
    for key in world.related_location.keys()[:-1]:
        world.page.is_text_present(world.related_location[key])

@step(u'When I assign a new investigator')
def when_i_assign_a_new_investigator(step):
    world.page.fill_in_with_js('$("#household-investigator")', world.investigator_1.id)

@step(u'Then I should see the investigator was saved successfully')
def then_i_should_see_the_investigator_was_saved_successfully(step):
    world.page.see_success_message('Household', 'edited')

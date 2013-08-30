from django.template.defaultfilters import slugify
from datetime import date
from lettuce import *
from rapidsms.contrib.locations.models import LocationType, Location
from survey.features.page_objects.household_member import NewHouseholdMemberPage
from survey.models import Household, Investigator

@step(u'And I have a household')
def and_i_have_a_household(step):
    world.household = Household.objects.create(investigator=world.investigator)


@step(u'And I visit new household member page')
def and_i_visit_new_household_member_page(step):
    world.page = NewHouseholdMemberPage(world.browser, world.household)
    world.page.visit()


@step(u'And I see all household member fields are present')
def and_i_see_all_household_member_fields_are_present(step):
    world.page.validate_fields()


@step(u'Then I should see member successfully created message')
def then_i_should_see_member_successfully_created_message(step):
    world.page.is_text_present('Household member successfully created.')


@step(u'And I fill all member related fields')
def and_i_fill_all_member_related_fields(step):
    data = {'name': 'xyz',
            'date_of_birth': '2013-08-30',
            'male': True
    }
    world.page.fill_valid_member_values(data)
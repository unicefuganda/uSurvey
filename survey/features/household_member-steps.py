from lettuce import *
from rapidsms.contrib.locations.models import LocationType, Location
from survey.features.page_objects.household_member import NewHouseholdMemberPage, EditHouseholdMemberPage
from survey.models import Household, HouseholdMember, Investigator


@step(u'And I have a household')
def and_i_have_a_household(step):
    district = LocationType.objects.get(slug = 'district')
    world.kampala = Location.objects.create(name='Kampala', type = district)
    world.investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=world.kampala)
    world.household = Household.objects.create(investigator=world.investigator, uid=4)


@step(u'And I visit new household member page')
def and_i_visit_new_household_member_page(step):
    world.page = NewHouseholdMemberPage(world.browser, world.household)
    world.page.visit()


@step(u'And I see all household member fields are present')
def and_i_see_all_household_member_fields_are_present(step):
    world.page.validate_fields()


@step(u'Then I should see member successfully created message')
def then_i_should_see_member_successfully_created_message(step):
    world.page.see_success_message('Household member', 'created')

@step(u'And I fill all member related fields')
def and_i_fill_all_member_related_fields(step):
    data = {'name': 'xyz',
            'date_of_birth': '2013-08-30',
            'male': True
    }
    world.page.fill_valid_member_values(data)


@step(u'And also I have a household member')
def and_also_i_have_a_household_member(step):
    world.household_member = HouseholdMember.objects.create(name='member1', date_of_birth='2013-08-30', male=True,
                                                            household=world.household)


@step(u'And I visit edit household member page')
def and_i_visit_edit_household_member_page(step):
    world.page = EditHouseholdMemberPage(world.browser, world.household, world.household_member)
    world.page.visit()


@step(u'And I see all details of household member are present')
def and_i_see_all_details_of_household_member_are_present(step):
    world.page.validate_member_details(world.household_member)


@step(u'And I edit member related fields')
def and_i_edit_member_related_fields(step):
    data = {'name': 'member1edited',
            'date_of_birth': '2013-08-31',
            'male': False
    }
    world.page.fill_valid_member_values(data)

@step(u'Then I should see member successfully edited message')
def then_i_should_see_member_successfully_edited_message(step):
    world.page.is_text_present('Household member successfully edited.')

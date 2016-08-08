from time import sleep
from lettuce import *
from rapidsms.contrib.locations.models import LocationType, Location
from survey.features.page_objects.household_member import NewHouseholdMemberPage, EditHouseholdMemberPage, DeleteHouseholdMemberPage
from survey.features.page_objects.households import HouseholdDetailsPage
from survey.models import EnumerationArea
from survey.models.households import HouseholdMember, HouseholdHead, Household
from survey.models.investigator import Investigator


@step(u'And I have a household')
def and_i_have_a_household(step):
    district = LocationType.objects.get(slug = 'district')
    world.kampala = Location.objects.create(name='Kampala', type=district)
    world.ea = EnumerationArea.objects.create(name="EA")
    world.ea.locations.add(world.kampala_village)
    world.investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", ea=world.ea)
    world.household = Household.objects.create(investigator=world.investigator, ea=world.investigator.ea, uid=4)
    HouseholdHead.objects.create(household=world.household, surname="Test", first_name="User",
                                 date_of_birth="1980-09-01", male=True,
                                 occupation='Agricultural labor', level_of_education='Primary',
                                 resident_since_year=2013, resident_since_month=2)


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
    data = {'surname': 'xyz',
            'male': True
            }

    world.page.fill_valid_member_values(data)
    world.page.select_date("#id_date_of_birth")
    sleep(3)

@step(u'And also I have a household member')
def and_also_i_have_a_household_member(step):
    world.household_member = HouseholdMember.objects.create(surname='member1', date_of_birth='2013-08-30', male=True,
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
    data = {'male': False,
            'surname': 'member1edited'
            }
    world.page.fill_valid_member_values(data)
    world.page.select_date("#id_date_of_birth")
    sleep(3)

@step(u'And I submit the form')
def and_i_submit_the_form(step):
    world.page.submit()

@step(u'Then I should see member successfully edited message')
def then_i_should_see_member_successfully_edited_message(step):
    world.page.is_text_present('Household member successfully edited.')


@step(u'And I visit that household details page')
def and_i_visit_that_household_details_page(step):
    world.page = HouseholdDetailsPage(world.browser, world.household)
    world.page.visit()

@step(u'And I click delete member')
def and_i_click_delete_member(step):
    world.page.click_delete_link(world.household_member.pk)

@step(u'Then I should see a confirmation modal')
def then_i_should_see_a_confirmation_modal(step):
    world.page = DeleteHouseholdMemberPage(world.browser, world.household, world.household_member)
    world.page.see_delete_confirmation_modal()

@step(u'Then that member is successfully deleted')
def then_that_member_is_successfully_deleted(step):
    world.page.see_success_message('Household member', 'deleted')
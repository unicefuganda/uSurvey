# -*- coding: utf-8 -*-
from time import sleep
from lettuce import step, world
from rapidsms.contrib.locations.models import LocationType
from survey.features.page_objects.upload_locations import UploadLocationsPage
from survey.models import LocationTypeDetails


@step(u'When I visit upload locations page')
def and_i_visit_upload_locations_page(step):
    world.page = UploadLocationsPage(world.browser)
    world.page.visit()

@step(u'And I have location type and location details objects')
def and_i_have_location_type_and_location_details_objects(step):
    world.location_type1 = LocationType.objects.create(name = 'type1',slug='type1')
    world.location_type_details1 = LocationTypeDetails.objects.create(required=False,has_code=False,code='',location_type=world.location_type1,country=world.country)

    world.location_type2 = LocationType.objects.create(name = 'type2',slug='type2')
    world.location_type_details2 = LocationTypeDetails.objects.create(required=False,has_code=False,code='',location_type=world.location_type2,country=world.country)

@step(u'Then I should see the text message')
def then_i_should_see_the_text_message(step):
    world.page.is_text_present('Upload Geographical Locations')

@step(u'And I should see name of the country for which details were added')
def and_i_should_see_name_of_the_country_for_which_details_were_added(step):
    world.page.find_by_css('#id_country',world.country.name)

@step(u'And I should see link for input file format')
def and_i_should_see_link_for_input_file_format(step):
    world.page.find_link_by_text("Location Input File Format")

@step(u'When I click on the link for input file format')
def when_i_click_on_the_link_for_input_file_format(step):
    world.page.click_link_by_text("Location Input File Format")

@step(u'Then I should see table of all location types')
def then_i_should_see_table_of_all_location_types(step):
    world.page.is_text_present(world.location_type1.name,True)
    world.page.is_text_present(world.location_type2.name,True)

@step(u'Then Table should collapse')
def then_table_should_collapse(step):
    sleep(2)
    world.page.is_text_present(world.location_type1.name,False)
    world.page.is_text_present(world.location_type2.name,False)

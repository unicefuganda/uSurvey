# -*- coding: utf-8 -*-
from lettuce import *
from rapidsms.contrib.locations.models import *

from survey.features.page_objects.locations import NewLocationTypePage, NewLocationPage


@step(u'And I visit new location type page')
def and_i_visit_new_location_type_page(step):
    world.page = NewLocationTypePage(world.browser)
    world.page.visit()

@step(u'And I see all location type fields are present')
def and_i_see_all_location_type_fields_are_present(step):
    world.page.validate_location_type_fields()

@step(u'And I fill all necessary location type fields')
def and_i_fill_all_necessary_location_type_fields(step):
    world.page.fill_valid_values({'name':'Taka'})

@step(u'Then I should see that the location type is created')
def then_i_should_see_that_the_location_type_is_created(step):
    world.page.see_success_message('Location Type', 'added')

@step(u'And I visit new location page')
def and_i_visit_new_location_page(step):
    world.page = NewLocationPage(world.browser)
    world.page.visit()

@step(u'And I have a location type')
def and_i_have_a_location_type(step):
    world.location_type = LocationType.objects.create(name = 'Country', slug='country')

@step(u'And I fill all necessary location fields')
def and_i_fill_all_necessary_location_fields(step):
    data = {'name': 'Uganda',
            'type': world.location_type.pk,
            }
    world.page.fill_valid_values(data)

@step(u'Then I should see that the location is created')
def then_i_should_see_that_the_location_is_created(step):
    world.page.see_success_message('Location', 'added')
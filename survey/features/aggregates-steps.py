# -*- coding: utf-8 -*-
from lettuce import *
from page_objects import *
from random import randint
from survey.models import *
from rapidsms.contrib.locations.models import *
from django.template.defaultfilters import slugify

@step(u'And I have 2 batches with one open')
def and_i_have_2_batches_with_one_open(step):
    survey = Survey.objects.create(name = "some survey")
    batch_1 = Batch.objects.create(order = 1, survey = survey)
    batch_2 = Batch.objects.create(order = 2, survey = survey)
    kampala_county = Location.objects.get(name = "Kampala County")
    batch_1.open_for_location(kampala_county)

@step(u'And I visit aggregate status page')
def and_i_visit_aggregate_status_page(step):
    world.page = AggregateStatusPage(world.browser)

@step(u'Then I should see an option to select location hierarchically')
def then_i_should_see_an_option_to_select_location_hierarchically(step):
    world.page.choose_location({'district': 'Kampala', 'county': 'Kampala County'})

@step(u'And I should see an option to select batch')
def and_i_should_see_an_option_to_select_batch(step):
    assert False, 'This step must be implemented'
@step(u'And I should see a get status button')
def and_i_should_see_a_get_status_button(step):
    assert False, 'This step must be implemented'
@step(u'And I have 2 investigators with households')
def and_i_have_2_investigators_with_households(step):
    assert False, 'This step must be implemented'
@step(u'And I choose a location and an open batch')
def and_i_choose_a_location_and_an_open_batch(step):
    assert False, 'This step must be implemented'
@step(u'And I click get status button')
def and_i_click_get_status_button(step):
    assert False, 'This step must be implemented'
@step(u'Then I should see number of households and clusters completed and pending')
def then_i_should_see_number_of_households_and_clusters_completed_and_pending(step):
    assert False, 'This step must be implemented'
@step(u'And I should see a list of investigators with corresponding phone numbers and pending households')
def and_i_should_see_a_list_of_investigators_with_corresponding_phone_numbers_and_pending_households(step):
    assert False, 'This step must be implemented'
@step(u'And I choose a location and a closed batch')
def and_i_choose_a_location_and_a_closed_batch(step):
    assert False, 'This step must be implemented'
@step(u'And I should see a message that says that this batch is currently closed')
def and_i_should_see_a_message_that_says_that_this_batch_is_currently_closed(step):
    assert False, 'This step must be implemented'

from page_objects import *
from lettuce import *
from survey.investigator_configs import *
from survey.models import *
from rapidsms.contrib.locations.models import *

@step(u'And I have a batch')
def and_i_have_prime_locations(step):
    world.batch = Batch.objects.create(order = 1, name = "Batch A",description='description')

@step(u'And I have prime locations')
def and_i_have_prime_locations(step):
    district = LocationType.objects.create(name=PRIME_LOCATION_TYPE, slug=PRIME_LOCATION_TYPE)
    world.districts = (
            Location.objects.create(name="Kampala", type=district),
            Location.objects.create(name="Abim", type=district),
    )

@step(u'And I visit batches listing page')
def and_i_visit_batches_listing_page(step):
    world.page = BatchListPage(world.browser)
    world.page.visit()

@step(u'And I visit the first batch listed')
def and_i_visit_the_first_batch_listed(step):
    world.page = world.page.visit_batch(world.batch)

@step(u'Then I should see all the prime locations with open close toggles')
def then_i_should_see_all_the_prime_locations_with_open_close_toggles(step):
    world.page.batch_closed_for_all_locations()

@step(u'When I open batch for a location')
def when_i_open_batch_for_a_location(step):
    world.page.open_batch_for(world.districts[1])

@step(u'Then I should see it is open for that location in db')
def then_i_should_see_it_is_open_for_that_location_in_db(step):
    assert BatchLocationStatus.objects.filter(location = world.districts[1]).count() == 1
    assert BatchLocationStatus.objects.filter(location = world.districts[0]).count() == 0

@step(u'When I close batch for a location')
def when_i_close_batch_for_a_location(step):
    world.page.close_batch_for(world.districts[1])

@step(u'Then I should see it is closed for that location in db')
def then_i_should_see_it_is_closed_for_that_location_in_db(step):
    assert BatchLocationStatus.objects.count() == 0

@step(u'And I click add batch button')
def and_i_click_add_batch_button(step):
    world.page.click_add_batch_button()

@step(u'Then I should see a add batch page')
def then_i_should_see_a_add_batch_page(step):
    world.page = AddBatchPage(world.browser)
    world.page.validate_url()

@step(u'When I fill the details for add batch form')
def when_i_fill_the_details_for_add_batch_form(step):
    data={'name':'hritik  batch',
          'description': 'roshan'}

    world.page.fill_valid_values(data)

@step(u'Then I should go back to batches listing page')
def then_i_should_go_back_to_batches_listing_page(step):
    world.page = BatchListPage(world.browser)
    world.page.validate_url()

@step(u'And I should see batch successfully added message')
def and_i_should_see_batch_successfully_added_message(step):
    world.page.see_batch_successfully_added_message()

@step(u'And I visit add batch page')
def and_i_visit_add_batch_page(step):
    world.page = AddBatchPage(world.browser)
    world.page.visit()

@step(u'Then I should see validation error messages')
def then_i_should_see_validation_error_messages(step):
    world.page.validate_error_message_on_fields()
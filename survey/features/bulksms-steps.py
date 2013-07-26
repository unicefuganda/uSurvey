from page_objects import *
from lettuce import *
from survey.investigator_configs import *
from survey.models import *

@step(u'And I have 2 districts with investigators')
def and_i_have_2_districts_with_investigators(step):
    district = LocationType.objects.create(name=SEND_BULK_SMS_TO_LOCATION_TYPE, slug='district')
    world.kampala = Location.objects.create(name="Kampala", type=district)
    world.abim = Location.objects.create(name="Abim", type=district)
    backend = Backend.objects.all()[0]
    Investigator.objects.create(name="Rajni", mobile_number="123456789", location=world.kampala, backend=backend)
    Investigator.objects.create(name="Rajni", mobile_number="123456780", location=world.abim, backend=backend)

@step(u'And I visit bulk SMS page')
def and_i_visit_bulk_sms_page(step):
    world.page = BulkSMSPage(world.browser)
    world.page.visit()

@step(u'And I compose a SMS to send')
def and_i_compose_a_sms_to_send(step):
    world.page.compose_message("MESSAGE")

@step(u'And I select the districts')
def and_i_select_the_districts(step):
    world.page.select_locations(world.kampala, world.abim)

@step(u'And I click send')
def and_i_click_send(step):
    world.page.submit()

@step(u'Then I should see a message saying SMS has been sent')
def then_i_should_see_a_message_saying_sms_has_been_sent(step):
    world.page.is_message_sent()
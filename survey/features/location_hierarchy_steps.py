from lettuce import step, world
from rapidsms.contrib.locations.models import Location, LocationType
from survey.features.page_objects.location_hierarchy import AddLocationHierarchyPage


@step(u'And I have a country')
def and_i_have_a_country(step):
    Location.objects.create(name='Some Country',type=LocationType.objects.create(name='country',slug='country'))

@step(u'And I visit add location hierarchy page')
def and_i_visit_add_location_hierarchy_page(step):
    world.page = AddLocationHierarchyPage(world.browser)
    world.page.visit()

@step(u'Then I should see text message')
def then_i_should_see_text_message(step):
    world.page.is_text_present('Create geographical location hierarchy')

@step(u'And I should see country dropdown')
def and_i_should_see_country_dropdown(step):
    assert world.browser.find_by_css('#id_country')

@step(u'And I should see country present in dropdown')
def and_i_should_see_country_present_in_dropdown(step):
    world.page.see_select_option(['Some Country'],'country')

@step(u'And I should see a row for level details field')
def and_i_should_see_a_row_for_level_details_field(step):
    world.browser.find_by_name('form-0-levels')
    world.browser.find_by_name('form-0-required')
    world.browser.find_by_name('form-0-has_code')
    world.browser.find_by_name('form-0-code')

@step(u'And I should see a link to add another row')
def and_i_should_see_a_link_to_add_another_row(step):
    world.page.find_link_by_text('add another')

@step(u'And I should see a link to remove a row')
def and_i_should_see_a_link_to_remove_a_row(step):
    world.page.find_link_by_text('remove')

@step(u'When I click add row link')
def when_i_click_add_row_link(step):
    world.page.click_link_by_text('add another')

@step(u'Then I should see anther row for levels details field')
def then_i_should_see_anther_row_for_levels_details_field(step):
    world.browser.find_by_name('form-1-levels')
    world.browser.find_by_name('form-1-required')
    world.browser.find_by_name('form-1-has_code')
    world.browser.find_by_name('form-1-code')

@step(u'When I click remove row link')
def when_i_click_remove_row_link(step):
    world.browser.find_by_css('.delete-row').last.click()

@step(u'Then I should see row for levels details field removed')
def then_i_should_see_row_for_levels_details_field_removed(step):
    world.page.field_not_present('form-0-levels')
    world.page.field_not_present('form-0-required')
    world.page.field_not_present('form-0-has_code')
    world.page.field_not_present('form-0-code')
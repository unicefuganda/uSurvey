from lettuce import step, world
from rapidsms.contrib.locations.models import Location, LocationType
from survey.features.page_objects.location_hierarchy import AddLocationHierarchyPage


@step(u'And I have a country')
def and_i_have_a_country(step):
    world.country = Location.objects.create(name='Some Country',type=LocationType.objects.create(name='country',slug='country'))

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
    world.page.see_field_details('Level 1', 'form-0')

@step(u'When I click add row icon')
def when_i_click_add_row_link(step):
    world.page.click_by_css(".icon-plus")

@step(u'Then I should see anther row for levels details field')
def then_i_should_see_anther_row_for_levels_details_field(step):
    world.page.see_field_details('Level 1', 'form-0')
    world.page.see_field_details('Level 2', 'form-1')

@step(u'When I click remove row icon')
def when_i_click_remove_row_link(step):
    world.browser.find_by_css('.icon-remove').last.click()

@step(u'Then I should see row for levels details field removed')
def then_i_should_see_row_for_levels_details_field_removed(step):
    world.page.see_field_details('Level 1', 'form-0')
    world.page.see_field_details('Level 2', 'form-1', False)

@step(u'And the code field is hidden')
def and_the_code_field_is_hidden(step):
    world.page.is_hidden('form-0-code')

@step(u'When I check has_code field')
def when_i_check_has_code_field(step):
    world.page.click_by_css('.has_code')

@step(u'Then code field is shown')
def then_code_field_is_shown(step):
    world.page.is_hidden('code', False)

@step(u'When I fill details')
def when_i_fill_details(step):
    data = {'country': world.country.id, 'form-0-levels': 'Region',
            'form-0-levels': 'Hill', 'form-0-required':'on',
            'form-0-has_code':'on', 'form-0-code':'0001',
            }
    world.page.fill_valid_values(data)

@step(u'And I click the create hierarchy button')
def and_i_click_the_create_hierarchy_button(step):
    world.page.submit()

@step(u'Then I should see location hierarchy successfully created')
def then_i_should_see_location_hierarchy_successfully_created(step):
    world.page.see_success_message('Location Hierarchy', 'created')

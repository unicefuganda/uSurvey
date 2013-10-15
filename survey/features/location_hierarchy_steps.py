from lettuce import step, world
from survey.features.page_objects.location_hierarchy import AddLocationHierarchyPage


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
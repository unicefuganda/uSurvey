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

@step(u'And I should see level1 text field')
def and_i_should_see_level1_text_field(step):
    assert world.browser.find_by_css('#id_levels')

@step(u'And I should see a plus icon')
def and_i_should_see_a_plus_icon(step):
    assert world.browser.find_by_css('.add-option')

@step(u'When I click add-level icon')
def when_i_click_add_level_icon(step):
    world.browser.find_by_css('.add-option').first.click()

@step(u'Then I should see another level field')
def then_i_should_see_another_level_field(step):
    assert len(world.browser.find_by_name('levels')) == 2

@step(u'And I should see another plus icon')
def and_i_should_see_another_plus_icon(step):
    assert len(world.browser.find_by_css('.add-option')) == 2

@step(u'And I should see remove icon')
def and_i_should_see_remove_icon(step):
    assert world.browser.find_by_css('.remove-option')

@step(u'When I click remove level icon')
def when_i_click_remove_level_icon(step):
    world.browser.find_by_css('.remove-option').first.click()

@step(u'Then I should see only one level field')
def then_i_should_see_only_one_level_field(step):
    assert len(world.browser.find_by_name('levels')) == 1

@step(u'And I should not see remove icon')
def and_i_should_not_see_remove_icon(step):
    assert not world.browser.find_by_css('.remove-option')
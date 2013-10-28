from lettuce import step, world
from survey.features.page_objects.indicators import NewIndicatorPage


@step(u'And I visit new indicator page')
def and_i_visit_new_indicator_page(step):
    world.page = NewIndicatorPage(world.browser)
    world.page.visit()


@step(u'And I fill in the indicator details')
def and_i_fill_in_the_indicator_details(step):
    form_data = {'module': world.health_module.id,
                 'name': 'Health',
                 'description': 'some description',
                 'measure': '%',
                 'batch': world.batch.id}
    world.page.fill_valid_values(form_data)

@step(u'Then I should see that the indicator was successfully added')
def then_i_should_see_that_the_indicator_was_successfully_added(step):
    world.page.see_success_message("Indicator", "created")
from lettuce import step, world
from survey.features.page_objects.indicators import NewIndicatorPage, ListIndicatorPage
from survey.models import QuestionModule, Batch, Indicator


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

@step(u'And I have two indicators')
def and_i_have_two_indicators(step):
    health_module = QuestionModule.objects.create(name="Health")
    batch = Batch.objects.create(name="Batch")
    world.indicator_1 = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
                                         module=health_module, batch=batch)
    world.indicator_2 = Indicator.objects.create(name="indicator name 2", description="rajni indicator 2", measure='Percentage',
                                         module=health_module, batch=batch)

@step(u'When I visit indicator listing page')
def when_i_visit_indicator_listing_page(step):
    world.page = ListIndicatorPage(world.browser)
    world.page.visit()


@step(u'Then I should see indicators listed')
def then_i_should_see_indicators_listed(step):
    list_titles = ['Indicator', 'Description', 'Module', 'Measure', 'Actions']
    values = [[field.name, field.description, field.module.name, field.measure] for field in [world.indicator_1, world.indicator_2]]
    values.append(list_titles)
    fields =[ field  for fields in values for field in fields]
    world.page.validate_fields_present(fields)
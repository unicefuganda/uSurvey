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


@step(u'Then I should see all indicators listed')
def then_i_should_see_indicators_listed(step):
    world.page.see_indicators([world.indicator_1, world.indicator_2, world.indicator_3])

@step(u'And I have three batches')
def and_i_have_three_batches(step):
    world.batch_1 = Batch.objects.create(name="New Batch 1", survey=world.survey)
    world.batch_2 = Batch.objects.create(name="New Batch 2", survey=world.survey)
    world.batch_3 = Batch.objects.create(name="New Batch 3")

@step(u'And I have an indicator not in that survey')
def and_i_have_an_indicator_not_in_that_survey(step):
    world.indicator_3 = Indicator.objects.create(name="indicator name 3", description="rajni indicator 3", measure='Percentage',
                                         module=world.health_module_1, batch=world.batch_3)

@step(u'And I have indicator in each batch')
def and_i_have_indicator_in_each_batch(step):
    world.indicator_1 = Indicator.objects.create(name="indicator name 1", description="rajni indicator 1", measure='Percentage',
                                         module=world.health_module_1, batch=world.batch_1)
    world.indicator_1b = Indicator.objects.create(name="indicator name with different module", description="rajni indicator 1", measure='Percentage',
                                         module=world.health_module_2, batch=world.batch_1)
    world.indicator_2 = Indicator.objects.create(name="indicator name 2", description="rajni indicator 2", measure='Percentage',
                                         module=world.health_module_2, batch=world.batch_2)

@step(u'When I select a survey')
def when_i_select_a_survey(step):
    world.page.select('survey', [world.survey.id])

@step(u'And I click on get list')
def and_i_click_on_get_list(step):
    world.page.click_by_css('#a-indicator-list')

@step(u'Then I should see indicators in that survey')
def then_i_should_see_indicators_in_that_survey(step):
    world.page.see_indicators([world.indicator_1,world.indicator_1b, world.indicator_2])
    world.page.is_text_present(world.indicator_3.name, False)

@step(u'When I select a batch')
def when_i_select_a_batch(step):
    world.page.select('batch', [world.batch_1.id])

@step(u'Then I should see indicators in that batch')
def then_i_should_see_indicators_in_that_batch(step):
    world.page.see_indicators([world.indicator_1, world.indicator_1b])
    world.page.is_text_present(world.indicator_2.name, False)
    world.page.is_text_present(world.indicator_3.name, False)

@step(u'And I have two modules')
def and_i_have_two_modules(step):
    world.health_module_1 = QuestionModule.objects.create(name="Module")
    world.health_module_2 = QuestionModule.objects.create(name="Module 2")

@step(u'When I select a module')
def when_i_select_a_module(step):
    world.page.select('module', [world.health_module_1.id])

@step(u'Then I should see indicators in that module')
def then_i_should_see_indicators_in_that_module(step):
    world.page.see_indicators([world.indicator_1])
    world.page.is_text_present(world.indicator_1b.name, False)
    world.page.is_text_present(world.indicator_2.name, False)
    world.page.is_text_present(world.indicator_3.name, False)

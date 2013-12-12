from time import sleep
from django.utils.datastructures import SortedDict
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
    world.indicator_1 = Indicator.objects.create(name="indicator name", description="rajni indicator",
                                                 measure='Percentage',
                                                 module=health_module, batch=batch)
    world.indicator_2 = Indicator.objects.create(name="indicator name 2", description="rajni indicator 2",
                                                 measure='Percentage',
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
    world.indicator_3 = Indicator.objects.create(name="indicator name 3", description="rajni indicator 3",
                                                 measure='Percentage',
                                                 module=world.health_module_1, batch=world.batch_3)


@step(u'And I have indicator in each batch')
def and_i_have_indicator_in_each_batch(step):
    world.indicator_1 = Indicator.objects.create(name="indicator name 1", description="rajni indicator 1",
                                                 measure='Percentage',
                                                 module=world.health_module_1, batch=world.batch_1)
    world.indicator_1b = Indicator.objects.create(name="indicator name with different module",
                                                  description="rajni indicator 1", measure='Percentage',
                                                  module=world.health_module_2, batch=world.batch_1)
    world.indicator_2 = Indicator.objects.create(name="indicator name 2", description="rajni indicator 2",
                                                 measure='Percentage',
                                                 module=world.health_module_2, batch=world.batch_2)


@step(u'When I select a survey')
def when_i_select_a_survey(step):
    world.page.select('survey', [world.survey.id])


@step(u'And I should see action buttons')
def and_i_should_see_action_buttons(step):
    world.page.validate_fields_present(["Delete", "Edit", "Formula", "Analysis"])


@step(u'And I click on get list')
def and_i_click_on_get_list(step):
    world.page.click_by_css('#a-indicator-list')


@step(u'Then I should see indicators in that survey')
def then_i_should_see_indicators_in_that_survey(step):
    world.page.see_indicators([world.indicator_1, world.indicator_1b, world.indicator_2])
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


@step(u'When I click on add indicator button')
def when_i_click_on_add_indicator_button(step):
    world.page.click_by_css('#add_indicator')


@step(u'Then I should see add indicator page')
def then_i_should_see_add_indicator_page(step):
    world.page = NewIndicatorPage(world.browser)
    world.page.validate_url()

@step(u'And I click the delete indicator link')
def and_i_click_the_delete_indicator_link(step):
    world.page.click_by_css("#delete-indicator_%s" % world.indicator_1.id)

@step(u'Then I should see confirm indicator batch')
def then_i_should_see_confirm_indicator_batch(step):
    world.page.see_confirm_modal_message(world.indicator_1.name)

@step(u'Then I should go back to indicator listing page')
def then_i_should_go_back_to_indicator_listing_page(step):
    world.page = ListIndicatorPage(world.browser)
    world.page.validate_url()

@step(u'And I should see the indicator successfully deleted')
def and_i_should_see_the_indicator_successfully_deleted(step):
    world.page.see_success_message("Indicator", "deleted")

@step(u'And I click the edit indicator link')
def and_i_click_the_edit_indicator_link(step):
    world.page.click_by_css("#edit-indicator_%s" % world.indicator_1.id)


@step(u'Then I should see the indicator details in the form')
def then_i_should_see_the_indicator_details_in_the_form(step):
    world.form_data = {'name': world.indicator_1.name,
                       'description': world.indicator_1.description,
                       'measure': '%'}
    world.page.validate_form_values(world.form_data)
    world.page.is_text_present(world.indicator_1.batch.name)
    world.page.is_text_present(world.indicator_1.module.name)

@step(u'When I fill in the new values for the indicator')
def when_i_fill_in_the_new_values_for_the_indicator(step):
    world.form_data = {'survey': world.survey.id,
                       'batch': world.batch_1.id,
                       'module': world.indicator_1.module.id,
                       'name': "Indicator new nme ",
                       'description': "Hoho description",
                       'measure': '%'}
    world.page.fill_valid_values(world.form_data)


@step(u'Then I should see the indicator successfully edited')
def then_i_should_see_the_indicator_successfully_edited(step):
    world.page.see_success_message("Indicator", 'edited')
# -*- coding: utf-8 -*-
from time import sleep
from lettuce import *
from django.utils.datastructures import SortedDict
from rapidsms.contrib.locations.models import *

from survey.features.page_objects.aggregates import AggregateStatusPage, DownloadExcelPage, InvestigatorReportPage
from survey.features.page_objects.survey_completion_rates import SurveyCompletionRatesPage
from survey.models import Survey
from survey.models.batch import Batch
from survey.models.households import Household
from survey.models.investigator import Investigator
from survey.models.formula import *
from survey import investigator_configs
from survey.views.survey_completion import _percent_completed_households


@step(u'And I have 2 batches with one open')
def and_i_have_2_batches_with_one_open(step):
    world.batch_1 = Batch.objects.create(order = 1, name = "Batch A")
    world.batch_2 = Batch.objects.create(order = 2, name = "Batch B")
    world.kampala_county = Location.objects.get(name = "Kampala County")
    world.someother_county = Location.objects.create(name = "Some County", tree_parent = world.kampala_county.tree_parent)
    world.batch_1.open_for_location(world.kampala_county.tree_parent)

@step(u'And I visit aggregate status page')
def and_i_visit_aggregate_status_page(step):
    world.page = AggregateStatusPage(world.browser)
    world.page.visit()

@step(u'Then I should see an option to select location hierarchically')
def then_i_should_see_an_option_to_select_location_hierarchically(step):
    world.page.choose_location({'district': 'Kampala', 'county': 'Kampala County'})

@step(u'And I should see an option to select batch')
def and_i_should_see_an_option_to_select_batch(step):
    world.page.check_if_batches_present(world.batch_1, world.batch_2)

@step(u'And I should see a get status button')
def and_i_should_see_a_get_status_button(step):
    world.page.check_get_status_button_presence()

@step(u'And I have 2 investigators with households')
def and_i_have_2_investigators_with_households(step):
    investigator = Investigator.objects.create(name="Rajini", mobile_number="123", location=world.kampala_county)
    investigator_2 = Investigator.objects.create(name="Batman", mobile_number="1234", location=world.someother_county)
    uid_counter = 0
    for index in range(investigator_configs.NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR):
        Household.objects.create(investigator = investigator, uid=uid_counter+index)
        Household.objects.create(investigator = investigator_2, uid=uid_counter+1+index)
        uid_counter = uid_counter + 2

    world.investigator = investigator
    world.investigator_2 = investigator_2

@step(u'And I choose a location and an open batch')
def and_i_choose_a_location_and_an_open_batch(step):
    locations = SortedDict()
    locations['district'] = 'Kampala'
    locations['county'] = 'Kampala County'
    world.page.choose_location(locations)
    world.page.choose_batch(world.batch_1)

@step(u'And I change my mind to select all districts')
def and_i_change_my_mind_to_select_all_districts(step):
    world.page.select_all_district()

@step(u'And I click get status button')
def and_i_click_get_status_button(step):
    world.page.submit()

@step(u'And I should see all districts as location selected')
def and_i_should_see_all_districts_location_selected(step):
    world.page.see_all_districts_location_selected()

@step(u'Then I should see number of households and clusters completed and pending')
def then_i_should_see_number_of_households_and_clusters_completed_and_pending(step):
    world.page.assert_status_count(pending_households=20, completed_housesholds=0, pending_clusters=2, completed_clusters=0)

@step(u'And I should see a list of investigators with corresponding phone numbers and pending households')
def and_i_should_see_a_list_of_investigators_with_corresponding_phone_numbers_and_pending_households(step):
    world.page.check_presence_of_investigators(world.investigator, world.investigator_2)

@step(u'And I choose a location and a closed batch')
def and_i_choose_a_location_and_a_closed_batch(step):
    world.page.choose_location({'district': 'Kampala'})
    world.page.choose_batch(world.batch_2)

@step(u'And I should see a message that says that this batch is currently closed')
def and_i_should_see_a_message_that_says_that_this_batch_is_currently_closed(step):
    world.page.assert_presence_of_batch_is_closed_message()

@step(u'And I have few batches')
def and_i_have_few_batches(step):
    world.batch = Batch.objects.create(order = 1, name = "Batch A")

@step(u'And I visit download excel page')
def and_i_visit_download_excel_page(step):
    world.page = DownloadExcelPage(world.browser)
    world.page.visit()

@step(u'And I select a batch and click export to csv')
def and_i_select_a_batch_and_click_export_to_csv(step):
    world.page.export_to_csv(world.batch)

@step(u'And I visit district aggregate page')
def and_i_visit_district_aggregate_page(step):
    world.page = SurveyCompletionRatesPage(world.browser)
    world.page.visit()

@step(u'Then I should see a table for completion rates')
def then_i_should_see_a_table_for_completion_rates(step):
    world.page.see_completion_rates_table()

@step(u'And I should see descendants in the table')
def and_i_should_see_descendants_in_the_table(step):
    world.page.is_text_present(world.kampala_subcounty.name)

@step(u'When I click on descendant name')
def when_i_click_on_descendant_name(step):
    world.page.click_link_by_text(world.kampala_subcounty.name)

@step(u'Then I should see status page for that location')
def then_i_should_see_status_page_for_that_location(step):
    world.page.see_completion_rates_table()
    world.page.is_text_present(world.kampala_parish.name)

@step(u'And I choose a village and an open batch')
def and_i_choose_a_village_and_an_open_batch(step):
    locations = SortedDict()
    locations['district'] = world.kampala_district.name
    locations['county'] = world.kampala_county.name
    locations['subcounty'] = world.kampala_subcounty.name
    locations['parish'] = world.kampala_parish.name
    locations['village'] = world.kampala_village.name

    world.page.choose_location(locations)
    world.page.choose_batch(world.batch_1)


@step(u'Then I should see a table for household completion rates')
def then_i_should_see_a_table_for_household_completion_rates(step):
    world.page.see_houdehold_completion_table()

@step(u'And I should see household details text')
def and_i_should_see_household_details_text(step):
    world.page.is_text_present("Survey Completion by household in %s %s" %(world.kampala_village.type.name, world.kampala_village.name))

@step(u'And I should see investigator details text')
def and_i_should_see_investigator_details_text(step):
    world.page.is_text_present('Investigator: %s(%s)' %(world.investigator.name, world.investigator.mobile_number))

@step(u'And I have an investigator and households')
def and_i_have_an_investigator_and_households(step):
    world.batch = Batch.objects.create()
    world.investigator = Investigator.objects.create(name="some_investigator", mobile_number="123456784", location=world.kampala_village)
    world.household_1 = Household.objects.create(investigator = world.investigator, uid=101, location=world.kampala_village)
    world.household_2 = Household.objects.create(investigator = world.investigator, uid=102, location=world.kampala_village)

@step(u'And I should see percent completion')
def and_i_should_see_percent_completion(step):
    world.page.is_text_present('Percent Completion: 0')

@step(u'And I have 2 surveys with one batch each')
def and_i_have_2_surveys_with_one_batch_each(step):
    world.survey_1 = Survey.objects.create(name='survey1', sample_size=10)
    world.survey_2 = Survey.objects.create(name='survey2', sample_size=10)
    world.batch_1 = Batch.objects.create(name='batch1', order=1, survey= world.survey_1)
    world.batch_2 = Batch.objects.create(name='batch2', order=1, survey= world.survey_2)

@step(u'When I select survey 2 from survey list')
def when_i_select_survey_2_from_survey_list(step):
    world.page.select('survey',[world.survey_2.id])

@step(u'Then I should see batch2 in batch list')
def then_i_should_see_batch2_in_batch_list(step):
    world.page.see_select_option([world.batch_2.name],'batch')

@step(u'And I should not see batch1 in batch list')
def and_i_should_not_see_batch1_in_batch_list(step):
    world.page.option_not_present([world.batch_1.name],'batch')

@step(u'When I select survey 1 from survey list')
def when_i_select_survey_1_from_survey_list(step):
    world.page.select('survey',[world.survey_1.id])

@step(u'Then I should see batch1 in batch list')
def then_i_should_see_batch1_in_batch_list(step):
    world.page.see_select_option([world.batch_1.name],'batch')

@step(u'And I should not see batch2 in batch list')
def and_i_should_not_see_batch2_in_batch_list(step):
    world.page.option_not_present([world.batch_2.name],'batch')

@step(u'And I should see title message')
def and_i_should_see_title_message(step):
    world.page.is_text_present('Survey Completion by Region/District')

@step(u'When I visit investigator report page')
def when_i_visit_investigator_report_page(step):
    world.page = InvestigatorReportPage(world.browser)
    world.page.visit()

@step(u'Then I should see title-text message')
def then_i_should_see_title_text_message(step):
    world.page.is_text_present('Choose survey to get investigators who completed the survey')

@step(u'And I should see dropdown with two surveys')
def and_i_should_see_dropdown_with_two_surveys(step):
    world.page.see_select_option([world.survey_1.name, world.survey_2.name], 'survey')

@step(u'And I should see generate report button')
def and_i_should_see_generate_report_button(step):
    assert world.browser.find_by_css("#download-investigator-form")[0].find_by_tag('button')[0].text == "Generate Report"
from random import randint

from lettuce import *
from survey.features.page_objects.batches import BatchListPage, AddBatchPage
from survey.models.surveys import Survey
from survey.features.page_objects.surveys import SurveyListPage, AddSurveyPage, EditSurveyPage


@step(u'And I visit surveys listing page')
def and_i_visit_surveys_listing_page(step):
    world.page = SurveyListPage(world.browser)
    world.page.visit()


@step(u'And I have 100 surveys')
def and_i_have_100_surveys(step):
    world.survey = list()
    for i in xrange(100):
        try:
            world.survey.append(Survey.objects.create(name='survey %d' % i, description='survey descrpition %d' % i,
                                                      type=(True if i % 2 else False), sample_size=i))
        except Exception:
            pass


@step(u'Then I should see the survey list paginated')
def then_i_should_see_the_survey_list_paginated(step):
    world.page.validate_fields()
    world.page.validate_pagination()
    world.page.validate_fields()


@step(u'And if I click the add survey button')
def and_if_i_click_the_add_survey_button(step):
    world.page.click_link_by_text("Create New Survey")


@step(u'Then I should see the new survey form')
def then_i_should_see_the_new_survey_form(step):
    world.page = AddSurveyPage(world.browser)
    world.page.validate_url()
    world.page.validate_fields_present(
        ["New Survey", "Name", "Description", "Type", "Number of Households"])


@step(u'And I visit the new survey page')
def and_i_visit_the_new_survey_page(step):
    world.page = AddSurveyPage(world.browser)
    world.page.visit()


@step(u'When I fill in the survey details')
def when_i_fill_in_the_survey_details(step):
    world.data = {'name': 'survey rajni',
                  'description': 'survey description rajni',
                  'sample_size': 10,
                  'type': True,
                  }
    world.page.fill_valid_values(world.data)


@step(u'And I select the questions')
def and_i_select_the_questions(step):
    world.page.select_multiple('#id_questions', world.question)


@step(u'Then I should see that the survey was saved successfully')
def then_i_should_see_that_the_survey_was_saved_successfully(step):
    world.page.see_success_message('Survey', 'added')


@step(u'And I have a survey')
def and_i_have_a_survey(step):
    world.survey = Survey.objects.create(
        name='survey name', description='survey descrpition', type=False, sample_size=10)


@step(u'And I click on a survey name')
def and_i_click_on_a_survey_name(step):
    world.page.click_link_by_text(world.survey.name)


@step(u'Then I should see a list of the batches under the survey')
def then_i_should_see_a_list_of_the_batches_under_the_survey(step):
    world.page = BatchListPage(world.browser, world.survey)
    world.page.validate_url()


@step(u'And I click on create new survey button')
def and_i_click_on_create_new_survey_button(step):
    world.page.click_link_by_partial_href("#new_survey")


@step(u'Then I should see the create new survey modal')
def then_i_should_see_the_create_new_survey_modal(step):
    world.page.validate_fields_present(
        ["New Survey", "Name", "Description", "Type", "Number of Households"])


@step(u'And I click the modal save button')
def and_i_click_the_modal_save_button(step):
    world.page.click_button("save_button")


@step(u'And when I click on add batch action for first survey')
def and_when_i_click_on_add_batch_action_for_first_survey(step):
    world.page = SurveyListPage(world.browser)
    world.page.visit()
    world.page.click_by_css(".add_batch")


@step(u'Then I should go to add batch page')
def then_i_should_go_to_add_batch_page(step):
    world.page = AddBatchPage(world.browser, world.survey[0])
    world.page.validate_url()


@step(u'And I click on edit link for this survey')
def and_i_click_on_edit_link_for_this_survey(step):
    world.page.click_link_by_text(" Edit")


@step(u'Then I should see the edit survey page')
def then_i_should_see_the_edit_survey_page(step):
    world.page = EditSurveyPage(world.browser, world.survey)
    world.page.validate_url()


@step(u'Then I should see that the survey was edited successfully')
def then_i_should_see_that_the_survey_was_edited_successfully(step):
    world.page.is_text_present(world.data['name'])
    world.page.see_success_message("Survey", "edited")


@step(u'And I click on delete link for this survey')
def and_i_click_on_delete_link_for_this_survey(step):
    world.page.click_link_by_text(" Delete")


@step(u'Then I should go back to survey listing page')
def then_i_should_go_back_to_survey_listing_page(step):
    world.page = SurveyListPage(world.browser)
    world.page.validate_url()


@step(u'And I should see that the survey was deleted successfully')
def and_i_should_see_that_the_survey_was_deleted_successfully(step):
    world.page.see_success_message("Survey", "deleted")


@step(u'Then I should see confirm delete survey')
def then_i_should_see_confirm_delete_survey(step):
    world.page.see_confirm_modal_message(world.survey.name)

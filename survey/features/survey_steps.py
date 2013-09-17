from random import randint

from lettuce import *
from survey.features.page_objects.batches import BatchListPage
from survey.models.surveys import Survey
from survey.features.page_objects.surveys import SurveyListPage, AddSurveyPage

@step(u'And I visit surveys listing page')
def and_i_visit_surveys_listing_page(step):
    world.page = SurveyListPage(world.browser)
    world.page.visit()

@step(u'And I have 100 surveys')
def and_i_have_100_surveys(step):
    for _ in xrange(100):
        random_number = randint(1, 99999)
        try:
            survey = Survey.objects.create(name='survey %d'%random_number, description= 'survey descrpition %d'%random_number, type=(True if random_number%2 else False), sample_size=random_number)
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
    world.page.validate_fields_present(["New Survey", "Name", "Description", "Type", "Sample size"])

@step(u'And I visit the new survey page')
def and_i_visit_the_new_survey_page(step):
    world.page = AddSurveyPage(world.browser)
    world.page.visit()

@step(u'When I fill in the survey details')
def when_i_fill_in_the_survey_details(step):
    data = {'name': 'survey rajni',
            'description': 'survey description rajni',
            'sample_size': 10,
            'type': True,
            }
    world.page.fill_valid_values(data)

@step(u'And I select the questions')
def and_i_select_the_questions(step):
    world.page.select_multiple('#id_questions', world.question)

@step(u'Then I should see that the survey was saved successfully')
def then_i_should_see_that_the_survey_was_saved_successfully(step):
    world.page.see_success_message('Survey', 'added')

@step(u'And I have a survey')
def and_i_have_a_survey(step):
    world.survey = Survey.objects.create(name='survey name', description= 'survey descrpition', type=False, sample_size=10)

@step(u'And I click on a survey name')
def and_i_click_on_a_survey_name(step):
    world.page.click_link_by_text(world.survey.name)

@step(u'Then I should see a list of the batches under the survey')
def then_i_should_see_a_list_of_the_batches_under_the_survey(step):
    world.page = BatchListPage(world.browser, world.survey)
    world.page.validate_url()

@step(u'And I click on create new survey button')
def and_i_click_on_create_new_survey_button(step):
    world.page.click_modal_link("#new_survey")

@step(u'Then I should see the create new survey modal')
def then_i_should_see_the_create_new_survey_modal(step):
    world.page.validate_fields_present(["New Survey", "Name", "Description", "Type", "Sample size"])

@step(u'And I click the modal save button')
def and_i_click_the_modal_save_button(step):
    world.page.click_button("save_button")

from random import randint
from lettuce import *
from survey.features.page_objects.question import QuestionsListPage, AddQuestionPage
from survey.models.question import Question
from survey.models.householdgroups import HouseholdMemberGroup

@step(u'And I have 100 questions under the batch')
def and_i_have_100_questions_under_the_batch(step):
    for _ in xrange(100):
        random_number = randint(1, 99999)
        try:
            Question.objects.create(batch=world.batch, text="some questions %d"%random_number,
                                                answer_type=Question.NUMBER, order=random_number)
        except Exception:
            pass

@step(u'And I visit questions listing page of the batch')
def and_i_visit_questions_listing_page_of_the_batch(step):
    world.page = QuestionsListPage(world.browser, world.batch)
    world.page.visit()

@step(u'Then I should see the questions list paginated')
def then_i_should_see_the_questions_list_paginated(step):
    world.page.validate_fields()
    world.page.validate_pagination()
    world.page.validate_fields()

@step(u'And I have no questions under the batch')
def and_i_have_no_questions_under_the_batch(step):
    Question.objects.filter(batch=world.batch).delete()

@step(u'Then I should see error message on the page')
def then_i_should_see_error_message_on_the_page(step):
    world.page.is_text_present("There are no questions associated with this batch yet.")

@step(u'And I click add question button')
def and_i_click_add_question_button(step):
    world.page.click_link_by_text("Add Question")

@step(u'Then I should see a add question page')
def then_i_should_see_a_add_question_page(step):
    world.page = AddQuestionPage(world.browser, world.batch)
    world.page.validate_url()

@step(u'When I fill the details for add question form')
def when_i_fill_the_details_for_add_question_form(step):
    data={'text':'hritik  question',
          'answer_type': Question.NUMBER}

    world.page.fill_valid_values(data)

@step(u'Then I should go back to questions listing page')
def then_i_should_go_back_to_questions_listing_page(step):
    world.page = QuestionsListPage(world.browser, world.batch)
    world.page.validate_url()


@step(u'And I should see question successfully added message')
def and_i_should_see_question_successfully_added_message(step):
    world.page.is_text_present("Question successfully added.")

@step(u'And I have a member group')
def and_i_have_a_member_group(step):
    world.household_member_group = HouseholdMemberGroup.objects.create(name='Age 4-5', order=1)

@step(u'And I visit add new question page of the batch')
def and_i_visit_add_new_question_page_of_the_batch(step):
    world.page = AddQuestionPage(world.browser,world.batch)
    world.page.visit()

@step(u'And I fill the details for question')
def and_i_fill_the_details_for_question(step):
    world.page.fill_valid_values({'text':'hritik  question'})
    world.page.select('group', [world.household_member_group.pk])

@step(u'When I select multichoice for answer type')
def when_i_select_multichoice_for_answer_type(step):
    world.page.select('answer_type', [Question.MULTICHOICE])

@step(u'Then I should see one option field')
def then_i_should_see_one_option_field(step):
    world.page.see_one_option_field("Option 1")
    world.page.see_option_add_and_remove_buttons(1)


@step(u'When I click add-option icon')
def when_i_click_add_option_icon(step):
    world.page.click_by_css(".icon-plus")

@step(u'Then I should see two options field')
def then_i_should_see_two_options_field(step):
    world.page.see_one_option_field("Option 1")
    world.page.see_one_option_field("Option 2")
    world.page.see_option_add_and_remove_buttons(2)

@step(u'When I click remove-option icon')
def when_i_click_remove_option_icon(step):
    world.page.click_by_css(".icon-remove")

@step(u'Then I should see only one option field')
def then_i_should_see_only_one_option_field(step):
    world.page.see_one_option_field("Option 1")
    world.page.see_option_add_and_remove_buttons(1)
    world.page.option_not_present("Option 2")

@step(u'And I fill an option question')
def and_i_fill_an_option_question(step):
    world.page.fill_valid_values({'options':'some option question text'})
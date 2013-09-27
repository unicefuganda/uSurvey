from time import sleep
from lettuce import *
from survey.features.page_objects.question import BatchQuestionsListPage
from survey.features.page_objects.rules import AddLogicToBatchQuestionPage
from survey.models import Question, AnswerRule
from survey.models.question import QuestionOption


def save_batch_to_question(question, batch):
    question.batch = batch
    question.save()
@step(u'And I have a question')
def and_i_have_a_question(step):
    world.question = Question.objects.create(text="question1", answer_type=Question.NUMBER, order=1)

@step(u'And I assign batch to these questions')
def and_i_assign_batch_to_these_questions(step):
    save_batch_to_question(world.question, world.batch)

@step(u'And I visit batches question list page')
def and_i_visit_batches_question_list_page(step):
    world.page = BatchQuestionsListPage(world.browser, world.batch)
    world.page.visit()

@step(u'And I click on add logic link')
def and_i_click_on_add_logic_link(step):
    sleep(15)
    world.page.click_link_by_text(" Add Logic")

@step(u'Then I should see the add logic page')
def then_i_should_see_the_add_logic_page(step):
    world.page = AddLogicToBatchQuestionPage(world.browser, world.question)
    world.page.validate_url()
    world.page.validate_fields()

@step(u'When I fill in skip rule details')
def when_i_fill_in_skip_rule_details(step):
    form_data={'condition': 'EQUALS',
               'attribute': 'value',
               'value': '0',
               'action': 'END_INTERVIEW',
               }
    world.page.fill_valid_values(form_data)

@step(u'Then I should see the logic was successfully added to the question')
def then_i_should_see_the_logic_was_successfully_added_to_the_question(step):
    world.page.see_success_message('Logic','added')

@step(u'And I assign batch to multichoice question')
def and_i_assign_batch_to_multichoice_question(step):
    world.question = world.multi_choice_question
    save_batch_to_question(world.question, world.batch)

@step(u'And I should see in multichoice if field defaulted to equals option')
def and_i_should_see_if_field_defaulted_to_equals_option(step):
    form_data = {'condition': 'EQUALS_OPTION'}
    world.page.validate_form_values(form_data)

@step(u'And I should see if field is disabled')
def and_i_should_see_if_field_is_disabled(step):
    assert world.page.is_disabled("id_condition")

@step(u'And I should see attribute field defaulted to option')
def and_i_should_see_attribute_field_defaulted_to_option(step):
    form_data = {'attribute': 'option'}
    world.page.validate_form_values(form_data)

@step(u'And I should see attribute field is disabled')
def and_i_should_see_attribute_field_is_disabled(step):
    assert world.page.is_disabled("id_attribute")

@step(u'And I should see dropdown of all available options')
def and_i_should_see_dropdown_of_all_available_options(step):
    options = [option.text for option in QuestionOption.objects.filter(question=world.question)]
    world.page.see_select_option(options, 'option')

@step(u'And I should not see value text box and questions dropdown')
def and_i_should_not_see_value_text_box_and_questions_dropdown(step):
    world.page.field_not_present('value')
    world.page.field_not_present('validate_with_question')

@step(u'When I select option from dropdown')
def when_i_select_option_from_dropdown(step):
    world.page.select('option', [world.option1.id])

@step(u'And I select skip to from then field')
def and_i_select_skip_to_from_then_field(step):
    world.page.select('action', ['SKIP_TO'])

@step(u'Then I should see field for next question next to the then field')
def then_i_should_see_field_for_next_question_next_to_the_then_field(step):
    assert world.page.field_is_visible('next_question')

@step(u'When I select end interview from then field')
def when_i_select_end_interview_from_then_field(step):
    world.page.select('action', ['END_INTERVIEW'])

@step(u'Then I should not see field for next question next to the then field')
def then_i_should_not_see_field_for_next_question_next_to_the_then_field(step):
    assert not world.page.field_is_visible('next_question')

@step(u'And I should see if field defaulted to equals')
def and_i_should_see_if_field_defaulted_to_equals(step):
    form_data = {'condition': 'EQUALS'}
    world.page.validate_form_values(form_data)


@step(u'And I should see if field is not disabled')
def and_i_should_see_if_field_is_not_disabled(step):
    assert not world.page.is_disabled("id_condition")

@step(u'And I should also have all other conditions in the dropdown')
def and_i_should_also_have_all_other_conditions_in_the_dropdown(step):
    condition_options =['GREATER_THAN_QUESTION','GREATER_THAN_VALUE','LESS_THAN_QUESTION','LESS_THAN_VALUE','EQUALS']
    world.page.see_select_option(condition_options, 'condition')

@step(u'And I should see attribute field defaulted to value')
def and_i_should_see_attribute_field_defaulted_to_value(step):
    form_data = {'attribute': 'value'}
    world.page.validate_form_values(form_data)


@step(u'And I should also have question in the attribute field dropdown')
def and_i_should_also_have_question_in_the_attribute_field_dropdown(step):
    world.page.see_select_option(['Value', 'Question'], 'attribute')

@step(u'And I should see attribute field is not disabled')
def and_i_should_see_attribute_field_is_not_disabled(step):
    assert not world.page.is_disabled("id_attribute")

@step(u'And I should see value text field')
def and_i_should_see_value_text_field(step):
    world.browser.find_by_name('value')
    assert world.page.field_is_visible('value')

@step(u'And I should not see option dropdown box and questions dropdown')
def and_i_should_not_see_option_dropdown_box_and_questions_dropdown(step):
    world.page.field_not_present('option')
    assert not world.page.field_is_visible('validate_with_question')

@step(u'When I select question option from dropdown')
def when_i_select_question_option_from_dropdown(step):
    world.page.select('attribute', ['validate_with_question'])

@step(u'Then I should see questions dropdown')
def then_i_should_see_questions_dropdown(step):
    assert world.page.field_is_visible('validate_with_question')

@step(u'And I should not see option dropdown box and value text box')
def and_i_should_not_see_option_dropdown_box_and_value_text_box(step):
    world.page.field_not_present('option')
    assert not world.page.field_is_visible('value')

@step(u'And I should see all the action dropdown options')
def and_i_should_see_all_the_action_dropdown_options(step):
    action_options =['REANSWER', 'END INTERVIEW', 'ASK SUBQUESTION', 'JUMP TO']
    world.page.see_select_option(action_options, 'action')

@step(u'And I have two subquestions for this question')
def and_i_have_two_subquestions_for_this_question(step):
    world.sub_question1 = Question.objects.create(batch=world.batch,text="sub question1", answer_type=Question.NUMBER, subquestion=True, parent=world.question)
    world.sub_question2 = Question.objects.create(batch=world.batch,text="sub question2", answer_type=Question.NUMBER, subquestion=True, parent=world.question)

@step(u'When I select ask subquestion from then field')
def when_i_select_ask_subquestion_from_then_field(step):
    world.page.select('action', ['ASK_SUBQUESTION'])

@step(u'Then I should see next question populated with subquestions')
def then_i_should_see_next_question_populated_with_subquestions(step):
    next_question_options =[world.sub_question1.text, world.sub_question2.text]
    world.page.see_select_option(next_question_options, 'next_question')
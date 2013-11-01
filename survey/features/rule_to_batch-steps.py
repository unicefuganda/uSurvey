from time import sleep
from lettuce import *
from survey.features.page_objects.question import BatchQuestionsListPage
from survey.features.page_objects.rules import AddLogicToBatchQuestionPage
from survey.models import Question, AnswerRule, BatchQuestionOrder
from survey.models.question import QuestionOption


def save_batch_to_question(question, batch):
    question.batches.add(batch)
    BatchQuestionOrder.objects.create(question=question, batch=batch, order=1)


@step(u'And I have a question')
def and_i_have_a_question(step):
    world.question = Question.objects.create(text="question1", answer_type=Question.NUMBER, order=1,
                                             group=world.household_member_group, module=world.module)


@step(u'And I assign batch to these questions')
def and_i_assign_batch_to_these_questions(step):
    save_batch_to_question(world.question, world.batch)


@step(u'And I visit batches question list page')
def and_i_visit_batches_question_list_page(step):
    world.page = BatchQuestionsListPage(world.browser, world.batch)
    world.page.visit()


@step(u'And I click on add logic link')
def and_i_click_on_add_logic_link(step):
    sleep(5)
    world.page.click_link_by_text(" Add Logic")


@step(u'Then I should see the add logic page')
def then_i_should_see_the_add_logic_page(step):
    world.page = AddLogicToBatchQuestionPage(world.browser, world.batch, world.question)
    world.page.validate_url()
    world.page.validate_fields()


@step(u'When I fill in skip rule details')
def when_i_fill_in_skip_rule_details(step):
    form_data = {'condition': 'EQUALS',
                 'attribute': 'value',
                 'value': '0',
                 'action': 'END_INTERVIEW',
    }
    world.page.fill_valid_values(form_data)


@step(u'Then I should see the logic was successfully added to the question')
def then_i_should_see_the_logic_was_successfully_added_to_the_question(step):
    world.page.see_success_message('Logic', 'added')


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
    condition_options = ['> QUESTION RESPONSE', '> VALUE', '< QUESTION RESPONSE', '< VALUE',
                         'EQUALS']
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
    action_options = ['RECONFIRM', 'END INTERVIEW', 'ASK SUBQUESTION', 'SKIP TO']
    world.page.see_select_option(action_options, 'action')


@step(u'And I have two subquestions for this question')
def and_i_have_two_subquestions_for_this_question(step):
    world.sub_question1 = Question.objects.create(text="sub question1", answer_type=Question.NUMBER, subquestion=True,
                                                  parent=world.question)
    world.sub_question2 = Question.objects.create(text="sub question2", answer_type=Question.NUMBER, subquestion=True,
                                                  parent=world.question)
    world.sub_question1.batches.add(world.batch)
    world.sub_question2.batches.add(world.batch)


@step(u'When I select ask subquestion from then field')
def when_i_select_ask_subquestion_from_then_field(step):
    world.page.select('action', ['ASK_SUBQUESTION'])


@step(u'Then I should see next question populated with subquestions')
def then_i_should_see_next_question_populated_with_subquestions(step):
    next_question_options = [world.sub_question1.text, world.sub_question2.text]
    world.page.see_select_option(next_question_options, 'next_question')


@step(u'Then I should see add subquestion button')
def then_i_should_see_add_subquestion_button(step):
    world.page.find_link_by_text("Add Subquestion")


@step(u'When I click add subquestion button')
def when_i_click_add_subquestion_button(step):
    world.page.click_link_by_text("Add Subquestion")


@step(u'Then I should see a modal for add subquestion')
def then_i_should_see_a_modal_for_add_subquestion(step):
    world.page.validate_fields_present(["New Sub Question", "Text", "Group", "Answer type"])


@step(u'When I fill the subquestion details')
def when_i_fill_the_subquestion_details(step):
    world.data = {'text': 'hritik question',
                  'answer_type': Question.NUMBER}

    world.page.fill_valid_values(world.data)


@step(u'And I click save question button on the form')
def and_i_click_save_question_button_on_the_form(step):
    world.page.click_by_css('#modal_sub_question_button')


@step(u'Then I should see the recent subquestion in next question dropdown')
def then_i_should_see_the_recent_subquestion_in_next_question_dropdown(step):
    sleep(2)
    world.page.see_select_option(world.data['text'], 'next_question')


@step(u'And I should not see the add subquestion button')
def and_i_should_not_see_the_add_subquestion_button(step):
    assert not world.page.field_is_visible("add_subquestion_button")


@step(u'And I should not the add subquestion button')
def and_i_should_not_the_add_subquestion_button(step):
    assert world.page.field_is_visible("add_subquestion_button")


@step(u'When I select greater than value from the drop down')
def when_i_select_greater_than_value_from_the_drop_down(step):
    world.page.select('condition', ['GREATER_THAN_VALUE'])


@step(u'Then I should see attribute field defaulted to value')
def then_i_should_see_attribute_field_defaulted_to_value(step):
    form_data = {'attribute': 'value'}
    world.page.validate_form_values(form_data)


@step(u'And I should not see question in the attribute')
def and_i_should_not_see_question_in_the_attribute(step):
    world.page.option_not_present(['Question'], 'attribute')


@step(u'When I select less than value from the drop down')
def when_i_select_less_than_value_from_the_drop_down(step):
    world.page.select('condition', ['LESS_THAN_VALUE'])


@step(u'When I select greater than question from the drop down')
def when_i_select_greater_than_question_from_the_drop_down(step):
    world.page.select('condition', ['GREATER_THAN_QUESTION'])


@step(u'Then I should see attribute field defaulted to question')
def then_i_should_see_attribute_field_defaulted_to_question(step):
    form_data = {'attribute': 'validate_with_question'}
    world.page.validate_form_values(form_data)


@step(u'And I should not see value in the attribute')
def and_i_should_not_see_value_in_the_attribute(step):
    world.page.option_not_present(['Value'], 'attribute')


@step(u'When I select less than question from the drop down')
def when_i_select_less_than_question_from_the_drop_down(step):
    world.page.select('condition', ['LESS_THAN_QUESTION'])


@step(u'When I select equals from drop down')
def when_i_select_equals_from_drop_down(step):
    world.page.select('condition', ['EQUALS'])


@step(u'And I should see question in the attribute')
def and_i_should_see_question_in_the_attribute(step):
    world.page.see_select_option(['Question'], 'attribute')


@step(u'And I have a subquestion under this question')
def and_i_have_a_subquestion_under_this_question(step):
    world.sub_question = Question.objects.create(subquestion=True, parent=world.question,
                                                 text="this is a subquestion")


@step(u'When I fill the  duplicate subquestion details')
def when_i_fill_the_duplicate_subquestion_details(step):
    world.page.fill_valid_values({'text': world.sub_question.text})
    world.page.select('group', [world.household_member_group.pk])
    world.page.select('answer_type', [Question.NUMBER])


@step(u'And I should see error on the form text field')
def and_i_should_see_error_on_the_form_text_field(step):
    sleep(5)
    world.page.is_text_present("Sub question for this question with this text already exists.")


@step(u'When I refill the form with valid values')
def when_i_refill_the_form_with_valid_values(step):
    world.data = {
        'text': world.sub_question.text + "edited text",
        'answer_type': Question.NUMBER,
        'group': world.household_member_group.pk
    }
    world.page.fill_valid_values({'text': world.data['text']})
    world.page.select('group', [world.data['group']])
    world.page.select('answer_type', [world.data['answer_type']])

@step(u'And I should see already existing logic for the question')
def and_i_should_see_already_existing_logic_for_the_question(step):
    world.page.validate_fields_present([world.question.text, "Eligibility Criteria", "Question/Value/Option", "Action"])

@step(u'When I select between from the drop down')
def when_i_select_between_from_the_drop_down(step):
    world.page.select('condition', ['BETWEEN'])

@step(u'And I should see two text fields for min and max value')
def and_i_should_see_two_text_fields_for_min_and_max_value(step):
    assert world.browser.find_by_css('#id_min_value')
    assert world.browser.find_by_css('#id_max_value')
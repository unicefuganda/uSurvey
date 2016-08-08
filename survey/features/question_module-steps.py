from lettuce import step, world
from survey.features.page_objects.question_module import QuestionModuleList, NewQuestionModule, EditQuestionModulePage
from survey.models import QuestionModule


@step(u'And I have two question modules')
def and_i_have_two_question_modules(step):
    world.health_module = QuestionModule.objects.create(name="Health")
    world.education_module = QuestionModule.objects.create(name="Education")

@step(u'When I visit the list questions modules page')
def when_i_visit_the_list_questions_modules_page(step):
    world.page = QuestionModuleList(browser=world.browser)
    world.page.visit()

@step(u'Then I should see the questions modules listed')
def then_i_should_see_the_questions_modules_listed(step):
    fields = [world.health_module.name, world.education_module.name, 'Number', 'Module Name', 'Module Lists']
    world.page.validate_fields_present(fields)

@step(u'When I visit the create questions module page')
def when_i_visit_the_create_questions_module_page(step):
    world.page = NewQuestionModule(world.browser)
    world.page.visit()
    world.page.validate_url()

@step(u'And I fill in the question module details')
def and_i_fill_in_the_question_module_details(step):
    world.page.fill_valid_values({'name': 'Education'})

@step(u'Then I should see that the question module on the listing page')
def then_i_should_see_that_the_question_module_on_the_listing_page(step):
    world.page = QuestionModuleList(browser=world.browser)
    fields = ['Education', 'Number', 'Module Name', 'Module Lists']
    world.page.validate_fields_present(fields)

@step(u'And I click delete module')
def and_i_click_delete_module(step):
    world.page.click_by_css("#delete-question-module_%s" % world.health_module.id)

@step(u'I should see a delete module confirmation modal')
def i_should_see_a_confirmation_modal(step):
    world.page.see_confirm_modal_message(world.health_module.name)

@step(u'When I confirm delete')
def when_i_confirm_delete(step):
    world.page.click_by_css("#delete-module-%s" % world.health_module.id)

@step(u'Then I should see the module was deleted')
def then_i_should_see_the_module_was_deleted(step):
    world.page.see_success_message("Module", "deleted")

@step(u'And I click edit module')
def and_i_click_edit_module(step):
    world.page.click_by_css("#edit-module_%s" % world.health_module.id)

@step(u'I should see a edit module page')
def i_should_see_a_edit_module_page(step):
    world.page = EditQuestionModulePage(world.browser, world.health_module)
    world.page.validate_url()

@step(u'When I fill in valid values')
def when_i_fill_in_valid_values(step):
    world.page.fill_valid_values({'name': 'Edited Module'})

@step(u'Then I should see the edited question module')
def then_i_should_see_the_edited_question_module(step):
    world.page = QuestionModuleList(world.browser)
    assert not world.page.browser.find_link_by_text(world.health_module.name)
    world.page.is_text_present('Edited Module')
    world.page.see_success_message("Question module", "edited")
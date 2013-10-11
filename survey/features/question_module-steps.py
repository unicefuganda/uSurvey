from lettuce import step, world
from survey.features.page_objects.question_module import QuestionModuleList, NewQuestionModule
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
    fields = [world.health_module.name, world.education_module.name, 'Number', 'Module Name', 'Question Module Lists']
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
    fields = ['Education', 'Number', 'Module Name', 'Question Module Lists']
    world.page.validate_fields_present(fields)
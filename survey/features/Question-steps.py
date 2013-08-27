from random import randint
from lettuce import *
from survey.features.page_objects.questions import QuestionsListPage
from survey.investigator_configs import *
from survey.models import *

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
    print world.page.url
    print world.page.url

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


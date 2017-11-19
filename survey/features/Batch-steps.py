from lettuce import *
from rapidsms.contrib.locations.models import *

from survey.features.page_objects.batches import AddBatchPage
from survey.features.page_objects.batches import AssignQuestionToBatchPage
from survey.features.page_objects.batches import BatchListPage
from survey.features.page_objects.batches import EditBatchPage
from survey.features.page_objects.question import BatchQuestionsListPage
from survey.features.page_objects.root import HomePage
from survey.investigator_configs import *
from survey.models import HouseholdMemberGroup, Survey
from survey.models.question import Question
from survey.models.batch import Batch, BatchLocationStatus


@step(u'And I have a batch')
def and_i_have_prime_locations(step):
    world.batch = Batch.objects.create(
        order=1,
        name="Batch A",
        description='description',
        survey=world.survey)


@step(u'And I have prime locations')
def and_i_have_prime_locations(step):
    district = LocationType.objects.create(
        name=PRIME_LOCATION_TYPE, slug=PRIME_LOCATION_TYPE)
    world.districts = (
        Location.objects.create(name="Kampala", type=district),
        Location.objects.create(name="Abim", type=district),
    )


@step(u'And I visit batches listing page')
def and_i_visit_batches_listing_page(step):
    world.page = BatchListPage(world.browser, world.survey)
    world.page.visit()


@step(u'And I visit the first batch listed')
def and_i_visit_the_first_batch_listed(step):
    world.page = world.page.visit_batch(world.batch)


@step(u'Then I should see all the prime locations with open close toggles')
def then_i_should_see_all_the_prime_locations_with_open_close_toggles(step):
    world.page.batch_closed_for_all_locations()


@step(u'And I open batch for a location')
@step(u'When I open batch for a location')
def when_i_open_batch_for_a_location(step):
    world.page.open_batch_for(world.districts[1])


@step(u'Then I should see it is open for that location in db')
def then_i_should_see_it_is_open_for_that_location_in_db(step):
    assert BatchLocationStatus.objects.filter(
        location=world.districts[1]).count() == 1
    assert BatchLocationStatus.objects.filter(
        location=world.districts[0]).count() == 0


@step(u'When I close batch for a location')
def when_i_close_batch_for_a_location(step):
    world.page.close_batch_for(world.districts[1])


@step(u'Then I should see it is closed for that location in db')
def then_i_should_see_it_is_closed_for_that_location_in_db(step):
    assert BatchLocationStatus.objects.count() == 0


@step(u'And I click add batch button')
def and_i_click_add_batch_button(step):
    world.page.click_add_batch_button()


@step(u'Then I should see a add batch page')
def then_i_should_see_a_add_batch_page(step):
    world.page = AddBatchPage(world.browser, world.survey)
    world.page.validate_url()
    world.page.validate_fields_present(["New Batch", "Name", "Description"])


@step(u'When I fill the details for add batch form')
def when_i_fill_the_details_for_add_batch_form(step):
    data = {'name': 'hritik  batch',
            'description': 'roshan'}

    world.page.fill_valid_values(data)


@step(u'Then I should go back to batches listing page')
def then_i_should_go_back_to_batches_listing_page(step):
    world.page = BatchListPage(world.browser, world.survey)
    world.page.validate_url()


@step(u'And I should see batch successfully added message')
def and_i_should_see_batch_successfully_added_message(step):
    world.page.see_success_message('Batch', 'added')


@step(u'And I visit add batch page')
def and_i_visit_add_batch_page(step):
    world.page = AddBatchPage(world.browser, world.survey)
    world.page.visit()


@step(u'Then I should see validation error messages')
def then_i_should_see_validation_error_messages(step):
    world.page.validate_error_message_on_fields()


@step(u'And I have 100 batches')
def and_i_have_100_batches(step):
    for i in xrange(100):
        try:
            Batch.objects.create(
                order=i,
                name="Batch %d" %
                i,
                description='description %d' %
                i,
                survey=world.survey)
        except Exception:
            pass


@step(u'And I should see the batches list paginated')
def and_i_should_see_the_batches_list_paginated(step):
    world.page.validate_fields()
    world.page.validate_pagination()
    world.page.validate_fields()


@step(u'And I click edit batch link')
def and_i_click_edit_batch_link(step):
    world.page.click_link_by_text(' Edit')


@step(u'Then I should see edit batch page')
def then_i_should_see_edit_batch_page(step):
    world.page = EditBatchPage(world.browser, world.batch, world.survey)
    world.page.validate_url()


@step(u'When I fill the details for the batch')
def when_i_fill_the_details_for_the_batch(step):
    data = {'name': 'hritik  batch',
            'description': 'roshan'}

    world.page.fill_valid_values(data)


@step(u'And I should see the batch successfully edited')
def and_i_should_see_the_batch_successfully_edited(step):
    world.page.see_success_message('Batch', 'edited')


@step(u'And I click delete batch link')
def and_i_click_delete_batch_link(step):
    world.page.click_link_by_text(' Delete')


@step(u'Then I should see confirm delete batch')
def then_i_should_see_confirm_delete_bacth(step):
    world.page.see_confirm_modal_message(world.batch.name)


@step(u'And if I click yes')
def and_if_i_click_yes(step):
    world.page.click_link_by_text('Yes')


@step(u'And I should see the batch successfully deleted')
def and_i_should_see_the_batch_successfully_deleted(step):
    world.page.see_success_message('Batch', 'deleted')


@step(u'And I click on batch name')
def and_i_click_on_batch_name(step):
    world.page.click_link_by_text(world.batch.name)


@step(u'Then I should be on the list of questions under the batch page')
def then_i_should_be_on_the_list_of_questions_under_the_batch_page(step):
    world.page = BatchQuestionsListPage(world.browser, world.batch)
    world.page.validate_url()


@step(u'And I click on assign question link')
def and_i_click_on_assign_question_link(step):
    world.page.click_link_by_text("Select Question")


@step(u'Then I should see the assign question page of that batch')
def then_i_should_see_the_assign_question_page_of_that_batch(step):
    world.page = AssignQuestionToBatchPage(world.browser, world.batch)
    world.page.validate_url()
    world.page.is_text_present(
        "Select Questions for %s - %s" %
        (world.survey.name.capitalize(),
         world.batch.name.capitalize()))


@step(u'When I select some questions')
def when_i_select_some_questions(step):
    world.page.select('questions', [world.question_1.pk, world.question_2.pk])


@step(u'Then I should see the questions successfully assigned to that batch')
def then_i_should_see_the_questions_successfully_assigned_to_that_batch(step):
    world.page.see_success_message(
        "Questions", "assigned to batch: %s" % world.batch.name.capitalize())


@step(u'And I have 2 questions')
def and_i_have_2_questions(step):
    world.question_1 = Question.objects.create(
        text="question1", answer_type=Question.NUMBER, order=1)
    world.question_2 = Question.objects.create(
        text="question2", answer_type=Question.TEXT, order=2)


@step(u'And I visit the assign question to page batch')
def and_i_visit_the_assign_question_to_page_batch(step):
    world.page = AssignQuestionToBatchPage(world.browser, world.batch)
    world.page.visit()


@step(u'When I select the group')
def when_i_select_the_group(step):
    world.page.select('group', [world.household_member_group.id])


@step(u'Then I should see the question which belong to that group')
def then_i_should_see_the_question_which_belong_to_that_group(step):
    world.page.see_the_question(True, world.question_1.id)
    world.page.see_the_question(False, world.question_2.id)


def create_question_for_group(group):
    return Question.objects.create(
        text="question-group%s" %
        group.name,
        answer_type=Question.NUMBER,
        group=group)


@step(u'And I have one question belonging to that group')
def and_i_have_one_question_belonging_to_that_group(step):
    world.question_1 = create_question_for_group(world.household_member_group)


@step(u'And another question which does not')
def and_another_question_which_does_not(step):
    world.question_2 = Question.objects.create(
        text="question2", answer_type=Question.TEXT)


@step(u'And I click add batch modal button')
def and_i_click_add_batch_modal_button(step):
    world.page.click_link_by_partial_href("#new_batch")


@step(u'Then I should see the add batch modal')
def then_i_should_see_the_add_batch_modal(step):
    world.page.validate_page_got_survey_id()
    world.page.validate_fields_present(["New Batch", "Name", "Description"])


@step(u'And I have 2 member groups')
def and_i_have_2_member_groups(step):
    world.household_member_group = HouseholdMemberGroup.objects.create(
        name='Age 4-5', order=1)
    world.member_group_2 = HouseholdMemberGroup.objects.create(
        name='Age 15-49', order=2)


@step(u'And I have questions belonging to those groups')
def and_i_have_questions_belonging_to_those_groups(step):
    world.question_1_with_group_1 = create_question_for_group(
        world.household_member_group)
    world.question_2_with_group_1 = create_question_for_group(
        world.household_member_group)
    world.question_1_with_group_2 = create_question_for_group(
        world.member_group_2)
    world.question_2_with_group_2 = create_question_for_group(
        world.member_group_2)


@step(u'And I select a question from the list')
def and_i_select_a_question_from_the_list(step):
    world.page.select_multiple("#id_questions", world.question_1_with_group_2)


@step(u'Then I should see in selected list the question which belong to that group')
def then_i_should_see_in_selected_list_the_question_which_belong_to_that_group(
        step):
    world.page.see_the_question(True, world.question_1_with_group_1.id)
    world.page.see_the_question(True, world.question_2_with_group_1.id)
    world.page.see_the_question(False, world.question_2_with_group_2.id)


@step(u'And I should see the previously selected questions on the page')
def and_i_should_see_the_previously_selected_questions_on_the_page(step):
    world.page.see_the_selected_question(
        True, world.question_1_with_group_2.id)


@step(u'When I fill the same name of the batch')
def when_i_fill_the_same_name_of_the_batch(step):
    world.page.fill('name', world.batch.name)
    world.page.fill('description', 'some description')


@step(u'Then I should see batch name already exists error message')
def then_i_should_see_batch_name_already_exists_error_message(step):
    world.page.is_text_present("Batch with the same name already exists.")


@step(u'And If I have an open batch in another survey in this location')
def and_if_i_have_an_open_batch_in_another_survey_in_this_location(step):
    world.survey1 = Survey.objects.create(
        name='another survey',
        description='another survey descrpition',
        type=False,
        sample_size=10)
    batch = Batch.objects.create(
        order=1,
        name="Batch B",
        description='description',
        survey=world.survey1)
    batch.open_for_location(world.districts[1])


@step(u'Then I should see an error that another batch from another survey is already open')
def then_i_should_see_an_error_that_another_batch_from_another_survey_is_already_open(
        step):
    open_batch_error_message = "%s has already open batches from survey %s" % (
        world.districts[1].name, world.survey1.name)
    world.page.is_text_present(open_batch_error_message)


@step(u'And I should not be able to open this batch')
def and_i_should_not_be_able_to_open_this_batch(step):
    world.page.is_disabled("open_close_switch_%s" % world.districts[1].id)


@step(u'When I activate non response for batch and location')
def when_i_activate_non_response_for_batch_and_location(step):
    world.page.activate_non_response_for_batch_and(world.districts[1])


@step(u'Then I should see it is activated for that location in db')
def then_i_should_see_it_is_activated_for_that_location_in_db(step):
    assert world.batch.non_response_is_activated_for(
        world.districts[0]) is True
    assert world.batch.non_response_is_activated_for(
        world.districts[1]) is False


@step(u'When I deactivate non response for batch and location')
def when_i_deactivate_non_response_for_batch_and_location(step):
    world.page.deactivate_non_response_for_batch_and(world.districts[0])


@step(u'Then I should see it is deactivated for that location in db')
def then_i_should_see_it_is_deactivated_for_that_location_in_db(step):
    assert world.batch.non_response_is_activated_for(
        world.districts[0]) is False
    assert world.batch.non_response_is_activated_for(
        world.districts[1]) is False


@step(u'Then I should see message batch is closed that location')
def then_i_should_see_message_batch_is_closed_that_location(step):
    world.page.is_text_present("%s is not open for %s" %
                               (world.batch.name, world.districts[1]))


@step(u'And I should not be able to activate this batch')
def and_i_should_not_be_able_to_activate_this_batch(step):
    world.page.is_disabled("open_close_switch_%s" % world.districts[1].id)


@step(u'When I open batch for a different location')
def when_i_open_batch_for_a_different_location(step):
    world.batch.open_for_location(world.districts[0])


@step(u'And I activate non response for that location')
def and_i_activate_non_response_for_that_location(step):
    world.page.activate_non_response_for_batch_and(world.districts[0])


@step(u'When I visit the home page')
def when_i_visit_the_home_page(step):
    world.page = HomePage(world.browser)
    world.page.visit()


@step(u'Then I should see that it is still activated')
def then_i_should_see_that_it_is_still_activated_for_that_location_in_db(step):
    world.page.is_text_present("On")


@step(u'When I close the batch of the other survey')
def when_i_close_the_batch_of_the_other_survey(step):
    world.batch.close_for_location(world.districts[1])


@step(u'Then the non-response switch for that location is active')
def then_the_non_response_switch_for_that_location_is_active(step):
    world.page.is_disabled('activate_non_response_switch_%d' % world.batch.id)
    world.page.is_text_present("%s is not open for %s" % (
        world.batch.name, world.districts[1]), False)

# -*- coding: utf-8 -*-
from lettuce import *
from rapidsms.contrib.locations.models import *

from survey.features.page_objects.batches import FormulaShowPage
from survey.models.batch import Batch
from survey.models.households import HouseholdHead, Household
from survey.models.backend import Backend
from survey.models.investigator import Investigator
from survey.models.formula import *
from survey.models.question import Question, QuestionOption


@step(u'And I have hierarchical locations with district and village')
def and_i_have_hierarchical_locations_with_district_and_village(step):
    district = LocationType.objects.create(name = 'District', slug = 'district')
    village = LocationType.objects.create(name = 'Village', slug = 'village')

    world.kampala = Location.objects.create(name='Kampala', type = district)
    world.village_1 = Location.objects.create(name='Village 1', type = village, tree_parent = world.kampala)
    world.village_2 = Location.objects.create(name='Village 2', type = village, tree_parent = world.kampala)

@step(u'And I have investigators completed batches')
def and_i_have_investigators_completed_batches(step):
    backend = Backend.objects.create(name='something')
    investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=world.village_1, backend = backend, weights = 0.3)
    household_1 = Household.objects.create(investigator=investigator, uid=6)
    household_2 = Household.objects.create(investigator=investigator, uid=7)
    household_3 = Household.objects.create(investigator=investigator, uid=8)

    investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", location=world.village_2, backend = backend, weights = 0.9)
    household_4 = Household.objects.create(investigator=investigator_1, uid=9)
    household_5 = Household.objects.create(investigator=investigator_1, uid=10)
    household_6 = Household.objects.create(investigator=investigator_1, uid=11)

    world.batch = Batch.objects.create(order=1)
    world.question_1 = Question.objects.create(batch=world.batch, text="Question 1?", answer_type=Question.NUMBER, order=1)
    world.question_2 = Question.objects.create(batch=world.batch, text="Question 2?", answer_type=Question.NUMBER, order=2)
    world.question_3 = Question.objects.create(batch=world.batch, text="This is a question", answer_type=Question.MULTICHOICE, order=3)
    option_1 = QuestionOption.objects.create(question=world.question_3, text="OPTION 2", order=1)
    option_2 = QuestionOption.objects.create(question=world.question_3, text="OPTION 1", order=2)

    world.formula_1 = Formula.objects.create(name="Name", numerator=world.question_1, denominator=world.question_2, batch=world.batch)
    world.formula_2 = Formula.objects.create(name="Name 1", numerator=world.question_3, denominator=world.question_1, batch=world.batch)

    investigator.answered(world.question_1, household_1, 20)
    investigator.answered(world.question_2, household_1, 20)
    investigator.answered(world.question_3, household_1, 1)

    investigator.answered(world.question_1, household_2, 10)
    investigator.answered(world.question_2, household_2, 20)
    investigator.answered(world.question_3, household_2, 1)

    investigator.answered(world.question_1, household_3, 30)
    investigator.answered(world.question_2, household_3, 30)
    investigator.answered(world.question_3, household_3, 2)

    investigator_1.answered(world.question_1, household_4, 30)
    investigator_1.answered(world.question_2, household_4, 30)
    investigator_1.answered(world.question_3, household_4, 2)

    investigator_1.answered(world.question_1, household_5, 20)
    investigator_1.answered(world.question_2, household_5, 20)
    investigator_1.answered(world.question_3, household_5, 2)

    investigator_1.answered(world.question_1, household_6, 40)
    investigator_1.answered(world.question_2, household_6, 40)
    investigator_1.answered(world.question_3, household_6, 1)

    for household in Household.objects.all():
        HouseholdHead.objects.create(household=household, surname="Surname %s" % household.pk)

@step(u'Given I am on the numerical answer computation page')
def given_i_am_on_the_numerical_answer_computation_page(step):
    world.page = FormulaShowPage(world.browser, world.formula_1)
    world.formula = world.formula_1
    world.page.visit()

@step(u'And I select a district to see results')
def and_i_select_a_district_to_see_results(step):
    world.page.choose_location(world.kampala)
    world.current_location = world.kampala
    world.page.submit()

@step(u'Then I should see the computed value')
def then_i_should_see_the_computed_value(step):
    world.page.presence_of_computed_value(world.formula.compute_for_location(world.current_location))

@step(u'And I should see the bar graph for all the villages')
def and_i_should_see_the_bar_graph_for_all_the_villages(step):
    world.page.presence_of_bar_graph_for_villages(world.formula_1.compute_for_next_location_type_in_the_hierarchy(current_location=world.kampala))

@step(u'And I select a village to see results')
def and_i_select_a_village_to_see_results(step):
    world.page.choose_location(world.kampala)
    world.page.choose_location(world.village_1)
    world.current_location = world.village_1
    world.page.submit()

@step(u'And I should see the bar graph for all the households')
def and_i_should_see_the_bar_graph_for_all_the_households(step):
    world.page.presence_of_bar_graph_for_households(world.formula_1.compute_for_households_in_location(world.village_1))

@step(u'Given I am on the multi choice answer computation page')
def given_i_am_on_the_multi_choice_answer_computation_page(step):
    world.page = FormulaShowPage(world.browser, world.formula_2)
    world.formula = world.formula_2
    world.page.visit()

@step(u'Then I should see the computed bar chart for all the options')
def then_i_should_see_the_computed_bar_chart_for_all_the_options(step):
    world.page.presence_of_bar_chart_for_all_the_options(world.formula.compute_for_location(world.current_location))

@step(u'And I should see the stacked bar graph for all the villages')
def and_i_should_see_the_stacked_bar_graph_for_all_the_villages(step):
    world.page.presence_of_stacked_bar_graph_for_villages(world.formula_2.compute_for_next_location_type_in_the_hierarchy(current_location=world.kampala))

@step(u'And I should see the tabulated results for all the households')
def and_i_should_see_the_tabulated_results_for_all_the_households(step):
    world.page.presence_of_tabulated_results_for_households(world.formula_2.compute_for_households_in_location(world.village_1))


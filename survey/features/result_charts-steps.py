# -*- coding: utf-8 -*-
from datetime import date
from lettuce import *
from rapidsms.contrib.locations.models import *

from survey.features.page_objects.batches import FormulaShowPage
from survey.models import GroupCondition, HouseholdMemberGroup, Indicator, QuestionModule
from survey.models.batch import Batch
from survey.models.households import HouseholdHead, Household, HouseholdMember
from survey.models.backend import Backend
from survey.models.investigator import Investigator
from survey.models.formula import *
from survey.models.question import Question, QuestionOption

def create_household_member(household):
    return HouseholdMember.objects.create(surname="Member", date_of_birth=date(1980, 2, 2), male=False, household=household)

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
    member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
    condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
    condition.groups.add(member_group)

    module = QuestionModule.objects.create(name="Education", description="Education Module")

    investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=world.village_1, backend = backend, weights = 0.3)
    household_1 = Household.objects.create(investigator=investigator, uid=6)
    household_2 = Household.objects.create(investigator=investigator, uid=7)
    household_3 = Household.objects.create(investigator=investigator, uid=8)

    investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", location=world.village_2, backend = backend, weights = 0.9)
    household_4 = Household.objects.create(investigator=investigator_1, uid=9)
    household_5 = Household.objects.create(investigator=investigator_1, uid=10)
    household_6 = Household.objects.create(investigator=investigator_1, uid=11)

    household_member_1 = create_household_member(household_1)
    household_member_2 = create_household_member(household_2)
    household_member_3 = create_household_member(household_3)
    household_member_4 = create_household_member(household_4)
    household_member_5 = create_household_member(household_5)
    household_member_6 = create_household_member(household_6)

    world.batch = Batch.objects.create(order=1)
    world.question_1 = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1, group=member_group, module=module)
    world.question_2 = Question.objects.create(text="Question 2?", answer_type=Question.NUMBER, order=2, group=member_group, module=module)
    world.question_3 = Question.objects.create(text="This is a question", answer_type=Question.MULTICHOICE, order=3, group=member_group, module=module)
    world.question_1.batches.add(world.batch)
    world.question_2.batches.add(world.batch)
    world.question_3.batches.add(world.batch)

    option_1 = QuestionOption.objects.create(question=world.question_3, text="OPTION 2", order=1)
    option_2 = QuestionOption.objects.create(question=world.question_3, text="OPTION 1", order=2)

    world.indicator = Indicator.objects.create(module=module, name='Indicator 1', measure=Indicator.MEASURE_CHOICES[0][0], batch=world.batch)
    world.formula_1 = Formula.objects.create(numerator=world.question_1, denominator=world.question_2, indicator=world.indicator)
    world.formula_2 = Formula.objects.create(numerator=world.question_3, denominator=world.question_1, indicator=world.indicator)

    investigator.member_answered(world.question_1, household_member_1, 20, world.batch)
    investigator.member_answered(world.question_2, household_member_1, 20, world.batch)
    investigator.member_answered(world.question_3, household_member_1, 1, world.batch)

    investigator.member_answered(world.question_1, household_member_2, 10, world.batch)
    investigator.member_answered(world.question_2, household_member_2, 20, world.batch)
    investigator.member_answered(world.question_3, household_member_2, 1, world.batch)

    investigator.member_answered(world.question_1, household_member_3, 30, world.batch)
    investigator.member_answered(world.question_2, household_member_3, 30, world.batch)
    investigator.member_answered(world.question_3, household_member_3, 2, world.batch)

    investigator_1.member_answered(world.question_1, household_member_4, 30, world.batch)
    investigator_1.member_answered(world.question_2, household_member_4, 30, world.batch)
    investigator_1.member_answered(world.question_3, household_member_4, 2, world.batch)

    investigator_1.member_answered(world.question_1, household_member_5, 20, world.batch)
    investigator_1.member_answered(world.question_2, household_member_5, 20, world.batch)
    investigator_1.member_answered(world.question_3, household_member_5, 2, world.batch)

    investigator_1.member_answered(world.question_1, household_member_6, 40, world.batch)
    investigator_1.member_answered(world.question_2, household_member_6, 40, world.batch)
    investigator_1.member_answered(world.question_3, household_member_6, 1, world.batch)

    for household in Household.objects.all():
        HouseholdHead.objects.create(household=household, surname="Surname %s" % household.pk, date_of_birth='2000-03-01')

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



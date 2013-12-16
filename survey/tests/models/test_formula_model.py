# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import date
from random import randint

from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.locations.models import LocationType

from survey.models import Batch, HouseholdMemberGroup, GroupCondition, Question, Formula, Backend, Investigator, Household, QuestionOption, Survey, EnumerationArea
from survey.models import HouseholdHead, Indicator, QuestionModule, Answer
from survey.models.households import HouseholdMember
from survey.tests.base_test import BaseTest


class FormulaTest(BaseTest):
    def setUp(self):
        self.batch = Batch.objects.create(order=1)
        self.member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)

        self.question_1 = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER,
                                                  order=1, group=self.member_group)
        self.question_2 = Question.objects.create(text="Question 2?", answer_type=Question.NUMBER,
                                                  order=2, group=self.member_group)
        self.question_1.batches.add(self.batch)
        self.question_2.batches.add(self.batch)

    def create_household_member(self, household):
        return HouseholdMember.objects.create(surname="Member", date_of_birth=date(1980, 2, 2), male=False,
                                              household=household)

    def create_household_head(self, uid, investigator):
        self.household = Household.objects.create(investigator=investigator, location=investigator.location,
                                                  uid=uid)
        return HouseholdHead.objects.create(household=self.household, surname="Name " + str(randint(1, 9999)),
                                            date_of_birth="1990-02-09")

    def test_store(self):
        formula = Formula.objects.create(numerator=self.question_1, denominator=self.question_2)
        self.failUnless(formula.id)

    def test_compute_answer_with_group_as_denominator(self):
        survey = Survey.objects.create(name="Sampled Survey")
        uganda = Location.objects.create(name="Uganda")
        kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
        abim = Location.objects.create(name="Abim", tree_parent=uganda)
        ea = EnumerationArea.objects.create(name="EA2", survey=survey)
        ea.locations.add(kampala)
        ea_2 = EnumerationArea.objects.create(name="EA2", survey=survey)
        ea_2.locations.add(abim)

        backend = Backend.objects.create(name='something')
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", ea=ea,
                                                   backend=backend, weights=0.3)
        household_1 = Household.objects.create(investigator=investigator, survey=survey, uid=1)
        household_2 = Household.objects.create(investigator=investigator, survey=survey, uid=2)

        investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", ea=ea_2,
                                                     backend=backend, weights=0.9)

        household_3 = Household.objects.create(investigator=investigator_1, survey=survey, uid=3)
        household_4 = Household.objects.create(investigator=investigator_1, survey=survey, uid=4)

        multi_choice_question = Question.objects.create(text="Question 2?", answer_type=Question.MULTICHOICE, order=2,
                                                       group=self.member_group)

        multi_choice_option_1 = QuestionOption.objects.create(question=multi_choice_question, text="Yes", order=1)
        multi_choice_option_2 = QuestionOption.objects.create(question=multi_choice_question, text="No", order=2)
        multi_choice_option_3 = QuestionOption.objects.create(question=multi_choice_question, text="Maybe", order=3)
        multi_choice_option_4 = QuestionOption.objects.create(question=multi_choice_question, text="Not Known", order=4)
        multi_choice_option_5 = QuestionOption.objects.create(question=multi_choice_question, text="N/A", order=5)
        multi_choice_option_6 = QuestionOption.objects.create(question=multi_choice_question, text="Ask", order=6)

        formula_numerator_options = [multi_choice_option_1, multi_choice_option_2, multi_choice_option_3]

        member_1 = self.create_household_member(household_1)
        member_2 = self.create_household_member(household_2)
        member_3 = self.create_household_member(household_3)
        member_4 = self.create_household_member(household_4)

        formula = Formula.objects.create(numerator=self.question_1, groups=self.member_group)
        another_formula = Formula.objects.create(numerator=multi_choice_question, groups=self.member_group)

        [another_formula.numerator_options.add(option) for option in formula_numerator_options]

        member_1_answer = 20
        member_2_answer = 10
        member_3_answer = 40
        member_4_answer = 50

        investigator_group_members = [member_1, member_2]
        investigator_1_group_members = [member_3, member_4]

        investigator.member_answered(self.question_1, member_1, member_1_answer, self.batch)
        investigator.member_answered(self.question_2, member_1, 200, self.batch)
        investigator.member_answered(multi_choice_question, member_1, 1, self.batch)
        investigator.member_answered(self.question_1, member_2, member_2_answer, self.batch)
        investigator.member_answered(self.question_2, member_2, 100, self.batch)
        investigator.member_answered(multi_choice_question, member_2, 2, self.batch)

        investigator_1.member_answered(self.question_1, member_3, member_3_answer, self.batch)
        investigator_1.member_answered(self.question_2, member_3, 400, self.batch)
        investigator_1.member_answered(multi_choice_question, member_3, 3, self.batch)
        investigator_1.member_answered(self.question_1, member_4, member_4_answer, self.batch)
        investigator_1.member_answered(self.question_2, member_4, 500, self.batch)
        investigator_1.member_answered(multi_choice_question, member_4, 4, self.batch)

        investigator_numerator_expected = (member_1_answer + member_2_answer)
        investigator_denominator_expected = len(investigator_group_members)

        investigator_1_numerator_expected = (member_3_answer + member_4_answer)
        investigator_1_denominator_expected = len(investigator_1_group_members)

        expected_answer = investigator_numerator_expected / investigator_denominator_expected

        self.assertEqual(investigator_denominator_expected, formula.denominator_computation(investigator, survey))
        self.assertEqual(investigator_numerator_expected, formula.numerator_computation(investigator, self.question_1))
        self.assertEqual(expected_answer, formula.compute_for_household_with_sub_options(survey, investigator))

        expected_answer = investigator_1_numerator_expected / investigator_1_denominator_expected

        self.assertEqual(investigator_1_denominator_expected, formula.denominator_computation(investigator_1, survey))
        self.assertEqual(investigator_1_numerator_expected, formula.numerator_computation(investigator_1, self.question_1))
        self.assertEqual(expected_answer, formula.compute_for_household_with_sub_options(survey, investigator_1))

        investigator_multi_choice_numerator = len([multi_choice_option_1, multi_choice_option_2])

        expected_answer = investigator_multi_choice_numerator/investigator_denominator_expected
        self.assertEqual(investigator_multi_choice_numerator, another_formula.numerator_computation(investigator,
                                                                                                    multi_choice_question))
        self.assertEqual(expected_answer, another_formula.compute_for_household_with_sub_options(survey, investigator))

        investigator_1_multi_choice_numerator = len([multi_choice_option_3])

        expected_answer = investigator_1_multi_choice_numerator/investigator_1_denominator_expected
        self.assertEqual(investigator_1_multi_choice_numerator, another_formula.numerator_computation(investigator_1,
                                                                                                    multi_choice_question))
        self.assertEqual(expected_answer, another_formula.compute_for_household_with_sub_options(survey, investigator_1))

    def test_compute_answer_with_multichoice_numerator_and_multichoice_denominator(self):
        survey = Survey.objects.create(name="Sampled Survey")
        uganda = Location.objects.create(name="Uganda")
        kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
        abim = Location.objects.create(name="Abim", tree_parent=uganda)
        backend = Backend.objects.create(name='something')
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=kampala,
                                                   backend=backend, weights=0.3)
        household_1 = Household.objects.create(investigator=investigator, survey=survey, uid=1)
        household_2 = Household.objects.create(investigator=investigator, survey=survey, uid=2)

        investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", location=abim,
                                                     backend=backend, weights=0.9)

        household_3 = Household.objects.create(investigator=investigator_1, survey=survey, uid=3)
        household_4 = Household.objects.create(investigator=investigator_1, survey=survey, uid=4)

        multi_choice_question = Question.objects.create(text="Question 2?", answer_type=Question.MULTICHOICE, order=2,
                                                       group=self.member_group)

        multi_choice_option_1 = QuestionOption.objects.create(question=multi_choice_question, text="Yes", order=1)
        multi_choice_option_2 = QuestionOption.objects.create(question=multi_choice_question, text="No", order=2)
        multi_choice_option_3 = QuestionOption.objects.create(question=multi_choice_question, text="Maybe", order=3)
        multi_choice_option_4 = QuestionOption.objects.create(question=multi_choice_question, text="Not Known", order=4)
        multi_choice_option_5 = QuestionOption.objects.create(question=multi_choice_question, text="N/A", order=5)
        multi_choice_option_6 = QuestionOption.objects.create(question=multi_choice_question, text="Ask", order=6)

        formula_numerator_options = [multi_choice_option_1, multi_choice_option_2, multi_choice_option_3]
        formula_denominator_options = [multi_choice_option_1, multi_choice_option_2, multi_choice_option_3,
                                       multi_choice_option_4, multi_choice_option_5, multi_choice_option_6]

        member_1 = self.create_household_member(household_1)
        member_2 = self.create_household_member(household_2)
        member_3 = self.create_household_member(household_3)
        member_4 = self.create_household_member(household_4)

        another_formula = Formula.objects.create(numerator=multi_choice_question, denominator=multi_choice_question)
        another_formula_count = Formula.objects.create(numerator=multi_choice_question, count=multi_choice_question)
        formula_denominator = Formula.objects.create(numerator=multi_choice_question, denominator=self.question_1)

        [another_formula.numerator_options.add(option) for option in formula_numerator_options]
        [another_formula.denominator_options.add(option) for option in formula_denominator_options]

        [another_formula_count.numerator_options.add(option) for option in formula_numerator_options]
        [another_formula_count.denominator_options.add(option) for option in formula_denominator_options]

        [formula_denominator.numerator_options.add(option) for option in formula_numerator_options]

        investigator.member_answered(multi_choice_question, member_1, 1, self.batch)
        investigator.member_answered(multi_choice_question, member_2, 2, self.batch)
        investigator.member_answered(self.question_1, member_1, 10, self.batch)
        investigator.member_answered(self.question_1, member_2, 40, self.batch)

        investigator_1.member_answered(multi_choice_question, member_3, 3, self.batch)
        investigator_1.member_answered(multi_choice_question, member_4, 4, self.batch)

        investigator_multi_choice_numerator = len([multi_choice_option_1, multi_choice_option_2])
        investigator_1_multi_choice_numerator = len([multi_choice_option_3])

        investigator_denominator_expected = 2
        investigator_1_denominator_expected = 2

        expected_answer = investigator_multi_choice_numerator/investigator_denominator_expected
        self.assertEqual(investigator_multi_choice_numerator, another_formula.numerator_computation(investigator,
                                                                                                    multi_choice_question))
        self.assertEqual(expected_answer, another_formula.compute_for_household_with_sub_options(survey, investigator))
        self.assertEqual(expected_answer, another_formula_count.compute_for_household_with_sub_options(survey, investigator))


        expected_answer = investigator_1_multi_choice_numerator/investigator_1_denominator_expected
        self.assertEqual(investigator_1_multi_choice_numerator, another_formula.numerator_computation(investigator_1,
                                                                                                    multi_choice_question))
        self.assertEqual(expected_answer, another_formula.compute_for_household_with_sub_options(survey, investigator_1))
        self.assertEqual(expected_answer, another_formula_count.compute_for_household_with_sub_options(survey, investigator_1))

        expected_answer = investigator_multi_choice_numerator/(10+40)
        self.assertEqual(expected_answer, formula_denominator.compute_for_household_with_sub_options(survey, investigator))

    def test_compute_numerical_answers(self):
        uganda = Location.objects.create(name="Uganda")
        kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
        abim = Location.objects.create(name="Abim", tree_parent=uganda)
        backend = Backend.objects.create(name='something')
        survey = Survey.objects.create(name="huhu")
        ea = EnumerationArea.objects.create(name="EA2", survey=survey)
        ea.locations.add(kampala)

        ea_2 = EnumerationArea.objects.create(name="EA2", survey=survey)
        ea_2.locations.add(abim)

        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", ea=ea,
                                                   backend=backend, weights=0.3)
        household_1 = Household.objects.create(investigator=investigator, uid=1)
        household_2 = Household.objects.create(investigator=investigator, uid=2)

        investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", ea=ea_2,
                                                     backend=backend, weights=0.9)
        household_3 = Household.objects.create(investigator=investigator_1, uid=3)
        household_4 = Household.objects.create(investigator=investigator_1, uid=4)

        member_1 = self.create_household_member(household_1)
        member_2 = self.create_household_member(household_2)
        member_3 = self.create_household_member(household_3)
        member_4 = self.create_household_member(household_4)

        formula = Formula.objects.create(numerator=self.question_1, denominator=self.question_2)
        investigator.member_answered(self.question_1, member_1, 20, self.batch)
        investigator.member_answered(self.question_2, member_1, 200, self.batch)
        investigator.member_answered(self.question_1, member_2, 10, self.batch)
        investigator.member_answered(self.question_2, member_2, 100, self.batch)

        investigator_1.member_answered(self.question_1, member_3, 40, self.batch)
        investigator_1.member_answered(self.question_2, member_3, 400, self.batch)
        investigator_1.member_answered(self.question_1, member_4, 50, self.batch)
        investigator_1.member_answered(self.question_2, member_4, 500, self.batch)

        self.assertEquals(formula.compute_for_location(kampala), 3)
        self.assertEquals(formula.compute_for_location(abim), 9)
        self.assertEquals(formula.compute_for_location(uganda), 6)

    def test_compute_multichoice_answer(self):
        uganda = Location.objects.create(name="Uganda")
        kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
        abim = Location.objects.create(name="Abim", tree_parent=uganda)
        backend = Backend.objects.create(name='something')
        survey = Survey.objects.create(name="huhu")
        ea = EnumerationArea.objects.create(name="EA2", survey=survey)
        ea.locations.add(kampala)
        abim_ea = EnumerationArea.objects.create(name="EA2", survey=survey)
        abim_ea.locations.add(abim)

        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", ea=ea,
                                                   backend=backend, weights=0.3)
        household_1 = Household.objects.create(investigator=investigator, uid=0)
        household_2 = Household.objects.create(investigator=investigator, uid=1)
        household_3 = Household.objects.create(investigator=investigator, uid=2)

        investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", ea=abim_ea,
                                                     backend=backend, weights=0.9)
        household_4 = Household.objects.create(investigator=investigator_1, uid=3)
        household_5 = Household.objects.create(investigator=investigator_1, uid=4)
        household_6 = Household.objects.create(investigator=investigator_1, uid=5)

        member_1 = self.create_household_member(household_1)
        member_2 = self.create_household_member(household_2)
        member_3 = self.create_household_member(household_3)
        member_4 = self.create_household_member(household_4)
        member_5 = self.create_household_member(household_5)
        member_6 = self.create_household_member(household_6)

        self.question_3 = Question.objects.create(text="This is a question",
                                                  answer_type=Question.MULTICHOICE, order=3, group=self.member_group)
        option_1 = QuestionOption.objects.create(question=self.question_3, text="OPTION 2", order=1)
        option_2 = QuestionOption.objects.create(question=self.question_3, text="OPTION 1", order=2)

        self.question_3.batches.add(self.batch)

        formula = Formula.objects.create(numerator=self.question_3, denominator=self.question_1)

        investigator.member_answered(self.question_1, member_1, 20, batch=self.batch)
        investigator.member_answered(self.question_3, member_1, 1, batch=self.batch)
        investigator.member_answered(self.question_1, member_2, 10, batch=self.batch)
        investigator.member_answered(self.question_3, member_2, 1, batch=self.batch)
        investigator.member_answered(self.question_1, member_3, 30, batch=self.batch)
        investigator.member_answered(self.question_3, member_3, 2, batch=self.batch)

        investigator_1.member_answered(self.question_1, member_4, 30, batch=self.batch)
        investigator_1.member_answered(self.question_3, member_4, 2, batch=self.batch)
        investigator_1.member_answered(self.question_1, member_5, 20, batch=self.batch)
        investigator_1.member_answered(self.question_3, member_5, 2, batch=self.batch)
        investigator_1.member_answered(self.question_1, member_6, 40, batch=self.batch)
        investigator_1.member_answered(self.question_3, member_6, 1, batch=self.batch)

        self.assertEquals(formula.compute_for_location(kampala), {option_1.text: 15, option_2.text: 15})
        self.assertEquals(formula.compute_for_location(abim), {option_1.text: 40, option_2.text: 50})
        self.assertEquals(formula.compute_for_location(uganda), {option_1.text: 27.5, option_2.text: 32.5})

    def test_get_group_formula_type(self):
        general_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=2)
        formula = Formula.objects.create(groups=general_group)

        self.assertEqual(general_group, formula.get_count_type())

    def test_get_count_formula_type(self):
        question_3 = Question.objects.create(text="This is a question",
                                                  answer_type=Question.MULTICHOICE, order=3)
        formula = Formula.objects.create(count=question_3)

        self.assertEqual(question_3, formula.get_count_type())



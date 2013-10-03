# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase
from rapidsms.contrib.locations.models import Location
from survey.models import Batch, HouseholdMemberGroup, GroupCondition, Question, Formula, Backend, Investigator, Household, QuestionOption
from survey.models.households import HouseholdMember


class FormulaTest(TestCase):
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

    def test_store(self):
        formula = Formula.objects.create(name="Name", numerator=self.question_1, denominator=self.question_2,
                                         batch=self.batch)
        self.failUnless(formula.id)

    def test_validation(self):
        batch_2 = Batch.objects.create(order=2)
        question_3 = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1)
        question_3.batches.add(batch_2)
        formula = Formula(name="Name", numerator=self.question_1, denominator=question_3, batch=self.batch)
        self.assertRaises(ValidationError, formula.save)

    def test_compute_numerical_answers(self):
        uganda = Location.objects.create(name="Uganda")
        kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
        abim = Location.objects.create(name="Abim", tree_parent=uganda)
        backend = Backend.objects.create(name='something')
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=kampala,
                                                   backend=backend, weights=0.3)
        household_1 = Household.objects.create(investigator=investigator, uid=1)
        household_2 = Household.objects.create(investigator=investigator, uid=2)

        investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", location=abim,
                                                     backend=backend, weights=0.9)
        household_3 = Household.objects.create(investigator=investigator_1, uid=3)
        household_4 = Household.objects.create(investigator=investigator_1, uid=4)

        member_1 = self.create_household_member(household_1)
        member_2 = self.create_household_member(household_2)
        member_3 = self.create_household_member(household_3)
        member_4 = self.create_household_member(household_4)

        formula = Formula.objects.create(name="Name", numerator=self.question_1, denominator=self.question_2,
                                         batch=self.batch)
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
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=kampala,
                                                   backend=backend, weights=0.3)
        household_1 = Household.objects.create(investigator=investigator, uid=0)
        household_2 = Household.objects.create(investigator=investigator, uid=1)
        household_3 = Household.objects.create(investigator=investigator, uid=2)

        investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", location=abim,
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
                                                  answer_type=Question.MULTICHOICE, order=3,group=self.member_group)
        option_1 = QuestionOption.objects.create(question=self.question_3, text="OPTION 2", order=1)
        option_2 = QuestionOption.objects.create(question=self.question_3, text="OPTION 1", order=2)

        self.question_3.batches.add(self.batch)

        formula = Formula.objects.create(name="Name", numerator=self.question_3, denominator=self.question_1, batch=self.batch)

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
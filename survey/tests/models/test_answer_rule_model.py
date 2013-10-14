# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import date
from django.test import TestCase
from rapidsms.contrib.locations.models import Location
from survey.models import Investigator, Backend, HouseholdMemberGroup, GroupCondition, Household, Batch, NumericalAnswer, Question, AnswerRule, QuestionOption, MultiChoiceAnswer
from survey.models.households import HouseholdMember


class AnswerRuleTest(TestCase):

    def setUp(self):
        self.location = Location.objects.create(name="Kampala")
        self.investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210",
                                                        location=self.location,
                                                        backend=Backend.objects.create(name='something'))

        self.member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)

        self.household = Household.objects.create(investigator=self.investigator, uid=0)

        self.household_member = HouseholdMember.objects.create(surname="Member",
                                                               date_of_birth=date(1980, 2, 2), male=False, household=self.household)
        self.batch = Batch.objects.create(order=1)
        self.batch.open_for_location(self.location)

    def test_numerical_equals_and_end_rule(self):
        NumericalAnswer.objects.all().delete()
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        next_question = self.investigator.member_answered(question_1, self.household_member, answer=1, batch=self.batch)
        self.assertEqual(next_question, question_2)

        NumericalAnswer.objects.all().delete()
        AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'],
                                         condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0)

        next_question = self.investigator.member_answered(question_1, self.household_member, answer=0, batch=self.batch)
        self.assertEqual(next_question, question_1)

        next_question = self.investigator.member_answered(question_1, self.household_member, answer=0, batch=self.batch)
        self.assertEqual(next_question, None)

    def test_numerical_equals_and_skip_to_rule(self):
        NumericalAnswer.objects.all().delete()
        question_1 = Question.objects.create(text="Question 1?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="Question 2?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_3 = Question.objects.create(text="Question 3?",
                                             answer_type=Question.NUMBER, order=3, group=self.member_group)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        question_3.batches.add(self.batch)
        next_question = self.investigator.member_answered(question_1, self.household_member, answer=1, batch=self.batch)
        self.assertEqual(next_question, question_2)

        NumericalAnswer.objects.all().delete()
        AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['SKIP_TO'],
                                         condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0,
                                         next_question=question_3)

        next_question = self.investigator.member_answered(question_1, self.household_member, answer=0, batch=self.batch)
        self.assertEqual(next_question, question_3)

    def test_numerical_greater_than_value_and_reanswer(self):
        NumericalAnswer.objects.all().delete()
        question_0 = Question.objects.create( text="How are you?", answer_type=Question.NUMBER,
                                             order=0, group=self.member_group)
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['REANSWER'],
                                         condition=AnswerRule.CONDITIONS['GREATER_THAN_VALUE'], validate_with_value=4)

        question_1.batches.add(self.batch)
        question_0.batches.add(self.batch)

        self.investigator.member_answered(question_0, self.household_member, answer=5, batch=self.batch)

        self.assertEqual(NumericalAnswer.objects.count(), 1)
        next_question = self.investigator.member_answered(question_1, self.household_member, answer=5, batch=self.batch)
        self.assertEqual(next_question, question_1)
        self.assertEqual(NumericalAnswer.objects.count(), 1)

        next_question = self.investigator.member_answered(question_1, self.household_member, answer=4, batch=self.batch)
        self.assertEqual(next_question, None)
        self.assertEqual(NumericalAnswer.objects.count(), 2)

    def test_numerical_greater_than_question_and_reanswer(self):
        NumericalAnswer.objects.all().delete()
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_3 = Question.objects.create(text="How many of them are children?",
                                             answer_type=Question.NUMBER, order=3, group=self.member_group)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        question_3.batches.add(self.batch)

        rule = AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['REANSWER'],
                                         condition=AnswerRule.CONDITIONS['GREATER_THAN_QUESTION'],
                                         validate_with_question=question_1)

        self.assertEqual(NumericalAnswer.objects.count(), 0)
        next_question = self.investigator.member_answered(question_1, self.household_member, answer=1, batch=self.batch)
        self.assertEqual(next_question, question_2)
        self.assertEqual(NumericalAnswer.objects.count(), 1)

        next_question = self.investigator.member_answered(question_2, self.household_member, answer=10, batch=self.batch)
        self.assertEqual(next_question, question_1)
        self.assertEqual(NumericalAnswer.objects.count(), 0)

    def test_numerical_less_than_value_and_reanswer(self):
        NumericalAnswer.objects.all().delete()
        question_0 = Question.objects.create(text="How are you?", answer_type=Question.NUMBER,
                                             order=0, group=self.member_group)
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)

        question_1.batches.add(self.batch)
        question_0.batches.add(self.batch)

        AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['REANSWER'],
                                         condition=AnswerRule.CONDITIONS['LESS_THAN_VALUE'], validate_with_value=4)

        self.investigator.member_answered(question_0, self.household_member, answer=5, batch=self.batch)

        self.assertEqual(NumericalAnswer.objects.count(), 1)
        next_question = self.investigator.member_answered(question_1, self.household_member, answer=3, batch=self.batch)
        self.assertEqual(next_question, question_1)
        self.assertEqual(NumericalAnswer.objects.count(), 1)

        next_question = self.investigator.member_answered(question_1, self.household_member, answer=4, batch=self.batch)
        self.assertEqual(next_question, None)
        self.assertEqual(NumericalAnswer.objects.count(), 2)

    def test_numerical_less_than_question_and_reanswer(self):
        NumericalAnswer.objects.all().delete()
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_3 = Question.objects.create(text="How many of them are children?",
                                             answer_type=Question.NUMBER, order=3, group=self.member_group)

        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        question_3.batches.add(self.batch)


        AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['REANSWER'],
                                         condition=AnswerRule.CONDITIONS['LESS_THAN_QUESTION'],
                                         validate_with_question=question_1)

        self.assertEqual(NumericalAnswer.objects.count(), 0)
        next_question = self.investigator.member_answered(question_1, self.household_member, answer=10, batch=self.batch)
        self.assertEqual(next_question, question_2)
        self.assertEqual(NumericalAnswer.objects.count(), 1)

        next_question = self.investigator.member_answered(question_2, self.household_member, answer=9, batch=self.batch)
        self.assertEqual(next_question, question_1)
        self.assertEqual(NumericalAnswer.objects.count(), 0)

    def test_multichoice_equals_option_and_ask_sub_question(self):
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.MULTICHOICE, order=1, group=self.member_group)
        QuestionOption.objects.create(question=question_1, text="OPTION 1", order=1)
        option_1_2 = QuestionOption.objects.create(question=question_1, text="OPTION 2", order=2)

        sub_question_1 = Question.objects.create(text="Specify others", answer_type=Question.TEXT,
                                                 subquestion=True, parent=question_1, group=self.member_group)

        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        for question in [question_1, question_2, sub_question_1]:
            self.batch.questions.add(question)

        AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                         condition=AnswerRule.CONDITIONS['EQUALS_OPTION'],
                                         validate_with_option=option_1_2, next_question=sub_question_1)

        next_question = self.investigator.member_answered(question_1, self.household_member, answer=1, batch=self.batch)
        self.assertEqual(next_question, question_2)

        MultiChoiceAnswer.objects.all().delete()

        next_question = self.investigator.member_answered(question_1, self.household_member, answer=2, batch=self.batch)
        self.assertEqual(next_question, sub_question_1)
        next_question = self.investigator.member_answered(sub_question_1, self.household_member, answer="Some explanation", batch=self.batch)
        self.assertEqual(next_question, question_2)

    def test_should_add_between_condition(self):
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)

        rule = AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'],
                                         condition=AnswerRule.CONDITIONS['BETWEEN'],
                                         validate_with_min_value=1, validate_with_max_value=10)
        self.failUnless(rule)
        self.batch.questions.add(question_1)
        next_question = self.investigator.member_answered(question_1, self.household_member, answer=4, batch=self.batch)
        self.assertEqual(next_question, question_1)

        next_question = self.investigator.member_answered(question_1, self.household_member, answer=4, batch=self.batch)
        self.assertIsNone(next_question)

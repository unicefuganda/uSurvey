from datetime import date
from random import randint
from django.core.exceptions import ValidationError

from django.test import TestCase
from survey.models.locations import LocationType, Location
from survey.models import GroupCondition, HouseholdHead, QuestionModule, Indicator, Formula, Survey, EnumerationArea
from django.db import IntegrityError
from survey.models.batch import Batch
from survey.models.backend import Backend
from survey.models.households import Household, HouseholdMember
from survey.models.interviewer import Interviewer
from survey.models.questions import Question, QuestionOption
from survey.models.householdgroups import HouseholdMemberGroup
from survey.tests.base_test import BaseTest


class QuestionTest(TestCase):

    def setUp(self):
        self.household_member_group = HouseholdMemberGroup.objects.create(
            name="test name1324", order=12)
        self.question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        self.batch = Batch.objects.create(order=1)

    def test_unicode_representation_of_question(self):
        question = Question.objects.create(identifier='123.1', text="This is a question", answer_type='Numerical Answer',
                                           group=self.household_member_group, batch=self.batch, module=self.question_mod)
        question_unicode = "%s - %s: (%s)" % (question.identifier,
                                              question.text, question.answer_type.upper())
        self.assertEqual(question_unicode, str(question))

    def test_numerical_question(self):
        question = Question.objects.create(identifier='13.1', text="This is a question!!!!!!", answer_type='Numerical Answer',
                                           group=self.household_member_group, batch=self.batch, module=self.question_mod)
        self.failUnless(question.id)

    def test_text_question(self):
        question = Question.objects.create(identifier='23.1', text="This is a question", answer_type='Text Answer',
                                           group=self.household_member_group, batch=self.batch, module=self.question_mod)
        self.failUnless(question.id)

    def test_variable_name_should_be_unique(self):
        question = Question.objects.create(identifier='143.1', text="This is a question", answer_type='Text Answer',
                                           group=self.household_member_group, batch=self.batch, module=self.question_mod)
        duplicate_question = Question(identifier='143.1', text="This is a question", answer_type='Text Answer',
                                      group=self.household_member_group, batch=self.batch, module=self.question_mod)
        self.assertRaises(IntegrityError, duplicate_question.save)

    def test_multichoice_question(self):
        household_member_group = HouseholdMemberGroup.objects.create(
            name="test name132", order=22)
        question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        batch = Batch.objects.create(order=1)
        question_1 = Question.objects.create(identifier='1.1', text="This is a question", answer_type='Numerical Answer',
                                             group=household_member_group, batch=batch, module=question_mod)

        question = Question.objects.create(identifier='14.1', text="This is a question32423", answer_type='Numerical Answer',
                                           group=household_member_group, batch=batch, module=question_mod)

        multi_choice_option_1 = QuestionOption.objects.create(
            question=question, text="Yes", order=1)
        multi_choice_option_2 = QuestionOption.objects.create(
            question=question, text="No", order=2)
        self.failUnless(question.id)

    def test_order(self):
        module = QuestionModule.objects.create(
            name="Health", description="some description")
        household_member_group = HouseholdMemberGroup.objects.create(
            name="test name2", order=2)
        batch = Batch.objects.create(order=1)
        question_2 = Question.objects.create(identifier='1.1', text="This is a question", answer_type='Numerical Answer',
                                             group=household_member_group, batch=batch, module=module)
        question_1 = Question.objects.create(identifier='1.2', text="How many of them are male?",
                                             answer_type="Numerical Answer", group=household_member_group, batch=batch,
                                             module=module)
        questions = Question.objects.all()
        self.assertEqual(questions[0], question_2)
        self.assertEqual(questions[1], question_1)

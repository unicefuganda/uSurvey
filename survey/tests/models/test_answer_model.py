from django.test import TestCase
from rapidsms.contrib.locations.models import Location
from survey.models import EnumerationArea

from survey.models.batch import Batch
from survey.models.backend import Backend
from survey.models.households import Household
from survey.models.investigator import Investigator
from survey.models.question import Question, QuestionOption, NumericalAnswer, TextAnswer, MultiChoiceAnswer


class NumericalAnswerTest(TestCase):
    def test_store(self):
        kampala = Location.objects.create(name="Kampala")
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(kampala)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210",
                                                   ea=ea,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        batch = Batch.objects.create(order=1)
        question = Question.objects.create(text="This is a question", answer_type=Question.NUMBER)
        question.batches.add(batch)
        answer = NumericalAnswer.objects.create(investigator=investigator, household=household, question=question,
                                                answer=10)
        self.failUnless(answer.id)


class TextAnswerTest(TestCase):
    def test_store(self):
        kampala = Location.objects.create(name="Kampala")
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(kampala)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210",
                                                   ea=ea,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        batch = Batch.objects.create(order=1)
        question = Question.objects.create(text="This is a question", answer_type=Question.TEXT)
        question.batches.add(batch)
        answer = TextAnswer.objects.create(investigator=investigator, household=household, question=question,
                                           answer="This is an answer")
        self.failUnless(answer.id)


class MultiChoiceAnswerTest(TestCase):
    def test_store(self):
        kampala = Location.objects.create(name="Kampala")
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(kampala)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210",
                                                   ea=ea,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        batch = Batch.objects.create(order=1)
        question = Question.objects.create(text="This is a question", answer_type=Question.MULTICHOICE)
        question.batches.add(batch)
        option = QuestionOption.objects.create(question=question, text="This is an option")

        answer = MultiChoiceAnswer.objects.create(investigator=investigator, household=household, question=question,
                                                  answer=option)
        self.failUnless(answer.id)

    def test_pagination(self):
        kampala = Location.objects.create(name="Kampala")
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(kampala)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210",
                                                   ea=ea,
                                                   backend=Backend.objects.create(name='something'))
        Household.objects.create(investigator=investigator, uid=0)
        batch = Batch.objects.create(order=1)
        question = Question.objects.create(text="This is a question", answer_type=Question.MULTICHOICE)
        question.batches.add(batch)
        option_1 = QuestionOption.objects.create(question=question, text="OPTION 1", order=1)
        option_2 = QuestionOption.objects.create(question=question, text="OPTION 2", order=2)
        option_3 = QuestionOption.objects.create(question=question, text="OPTION 3", order=3)
        option_4 = QuestionOption.objects.create(question=question, text="OPTION 4", order=4)
        option_5 = QuestionOption.objects.create(question=question, text="OPTION 5", order=5)
        option_6 = QuestionOption.objects.create(question=question, text="OPTION 6", order=6)
        option_7 = QuestionOption.objects.create(question=question, text="OPTION 7", order=7)
        back_text = Question.PREVIOUS_PAGE_TEXT
        next_text = Question.NEXT_PAGE_TEXT

        question_in_text = "%s\n1: %s\n2: %s\n3: %s\n%s" % (
            question.text, option_1.text, option_2.text, option_3.text, next_text)
        self.assertEqual(question.to_ussd(), question_in_text)

        question_in_text = "%s\n1: %s\n2: %s\n3: %s\n%s" % (
            question.text, option_1.text, option_2.text, option_3.text, next_text)
        self.assertEqual(question.to_ussd(1), question_in_text)

        question_in_text = "%s\n4: %s\n5: %s\n6: %s\n%s\n%s" % (
            question.text, option_4.text, option_5.text, option_6.text, back_text, next_text)
        self.assertEqual(question.to_ussd(2), question_in_text)

        question_in_text = "%s\n7: %s\n%s" % (question.text, option_7.text, back_text)
        self.assertEqual(question.to_ussd(3), question_in_text)



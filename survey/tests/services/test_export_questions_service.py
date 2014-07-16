from survey.services.export_questions import ExportQuestionsService

from survey.tests.base_test import BaseTest
from survey.models import Question, QuestionOption, HouseholdMemberGroup


class ExportQuestionsTest(BaseTest):

    def setUp(self):
        self.member_group = HouseholdMemberGroup.objects.create(name="old people", order=0)
        self.question1 = Question.objects.create(text="Question 1?", group=self.member_group,
                                                answer_type=Question.NUMBER, order=1, identifier='Q1')
        self.question2 = Question.objects.create(text="Question 2?", group=self.member_group,
                                                answer_type=Question.TEXT, order=2, identifier='Q2')
        self.question3 = Question.objects.create(text="Question 3?", group=self.member_group,
                                                answer_type=Question.MULTICHOICE, order=3, identifier='Q3')
        self.option1 = QuestionOption.objects.create(question=self.question3, text="option1", order=1)
        self.option2 = QuestionOption.objects.create(question=self.question3, text="option2", order=2)
        self.option3 = QuestionOption.objects.create(question=self.question3, text="option3", order=3)
        self.headings = "Question Text; Group; Answer Type; Options"

    def test_exports_questions_with_normal_group(self):

        question1 = "%s; %s; %s" %(self.question1.text, self.question1.group.name, self.question1.answer_type.upper())
        question2 = "%s; %s; %s" %(self.question2.text, self.question2.group.name, self.question2.answer_type.upper())
        question3_1 = "%s; %s; %s; %s" %(self.question3.text, self.question3.group.name,
                                         self.question3.answer_type.upper(), self.option1.text)
        question3_2 = "; ; ; %s" %(self.option2.text)
        question3_3 = "; ; ; %s" %(self.option3.text)

        expected_data = [self.headings, question1, question2, question3_1, question3_2, question3_3]

        export_questions_service = ExportQuestionsService()
        actual_data = export_questions_service.formatted_responses()

        self.assertEqual(len(expected_data), len(actual_data))
        self.assertIn(expected_data[0], actual_data)
        self.assertIn(expected_data[1], actual_data)
        self.assertIn(expected_data[2], actual_data)
        self.assertIn(expected_data[3], actual_data)
        self.assertIn(expected_data[4], actual_data)

from survey.services.export_questions import ExportQuestionsService, get_batch_question_as_dump,get_question_template_as_dump

from survey.tests.base_test import BaseTest
from survey.models import Question, QuestionOption, HouseholdMemberGroup, Batch, QuestionModule


class ExportQuestionsTest(BaseTest):

    def setUp(self):
        self.question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        self.batch = Batch.objects.create(order=1)
        self.member_group = HouseholdMemberGroup.objects.create(name="old people", order=0)
        self.question1 = Question.objects.create(identifier='1.1',text="This is a question1", answer_type='Numerical Answer',
                                           group=self.member_group,batch=self.batch,module=self.question_mod)
        self.question2 = Question.objects.create(identifier='1.2',text="This is a question2", answer_type='Text Answer',
                                           group=self.member_group,batch=self.batch,module=self.question_mod)
        self.question3 = Question.objects.create(identifier='1.3',text="This is a question3", answer_type='Numerical Answer',
                                           group=self.member_group,batch=self.batch,module=self.question_mod)
        self.option1 = QuestionOption.objects.create(question=self.question3, text="option1", order=1)
        self.option2 = QuestionOption.objects.create(question=self.question3, text="option2", order=2)
        self.option3 = QuestionOption.objects.create(question=self.question3, text="option3", order=3)
        self.headings = "Question Text; Group; Answer Type; Options"

    def test_exports_all_questions_with_normal_group(self):

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
        self.assertIn(str(expected_data[0]), actual_data)

    def test_exports_all_questions_in_a_batch(self):
        self.create_questions_not_in_batch()

        question1 = "%s; %s; %s" %(self.question1.text, self.question1.group.name, self.question1.answer_type.upper())
        question2 = "%s; %s; %s" %(self.question2.text, self.question2.group.name, self.question2.answer_type.upper())
        question3_1 = "%s; %s; %s; %s" %(self.question3.text, self.question3.group.name,
                                         self.question3.answer_type.upper(), self.option1.text)
        question3_2 = "; ; ; %s" %(self.option2.text)
        question3_3 = "; ; ; %s" %(self.option3.text)

        expected_data = [self.headings, question1, question2, question3_1, question3_2, question3_3]

        export_questions_service = ExportQuestionsService()
        actual_data = export_questions_service.formatted_responses()

        self.assertEqual(8, len(actual_data))
        self.assertIn(str(expected_data[0]), actual_data)



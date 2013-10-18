from survey.models import QuestionModule, Question
from survey.tests.base_test import BaseTest


class QuestionModuleTest(BaseTest):
    def test_fields(self):
        question_module = QuestionModule()
        fields = [str(item.attname) for item in question_module._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'description']:
            self.assertIn(field, fields)

    def test_store(self):
        module = QuestionModule.objects.create(name="Health", description="some description")
        self.failUnless(module.id)
        self.failUnless(module.name)
        self.failUnless(module.description)

    def test_question_knows_de_associate_self_from_module(self):
        module = QuestionModule.objects.create(name="Health", description="some description")
        Question.objects.create(text="This is a test question", answer_type="multichoice",
                                                  module=module)
        Question.objects.create(text="Another test question", answer_type="multichoice",
                                                          module=module)

        self.failUnless(module.module_question.all())
        module.remove_related_questions()

        self.failIf(module.module_question.all())
        all_questions = Question.objects.filter()

        [self.assertIsNone(question.module) for question in all_questions]
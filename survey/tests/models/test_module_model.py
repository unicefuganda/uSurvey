from survey.models import QuestionModule, Question, HouseholdMemberGroup, Batch
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
        household_member_group = HouseholdMemberGroup.objects.create(name="test name2", order=2)
        batch = Batch.objects.create(order=1)
        Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
                                           group=household_member_group,batch=batch,module=module)
        Question.objects.create(identifier='1.2',text="How many of them are male?",
                                             answer_type="Numerical Answer", group=household_member_group,batch=batch,
                                             module=module)
        module.remove_related_questions()
        all_questions = Question.objects.filter()
        [self.assertIsNotNone(question.module) for question in all_questions]

    def test_unicode_text(self):
        module = QuestionModule.objects.create(name="module name")
        self.assertEqual(module.name, str(module))
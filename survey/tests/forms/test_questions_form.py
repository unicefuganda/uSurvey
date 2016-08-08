from django.test import TestCase
from survey.forms.question import *
from survey.models import Batch, Survey
from survey.models.questions import Question
from survey.models.householdgroups import HouseholdMemberGroup


class QuestionFormTest(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(name="Test Survey",description="Desc",sample_size=10,has_sampling=True)
        self.household_member_group = HouseholdMemberGroup.objects.create(name='Age 4-5', order=1)
        self.question_module = QuestionModule.objects.create(name="Education")
        self.batch = Batch.objects.create(name='Batch A',description='description', survey=self.survey)
        self.question = Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
                                           group=self.household_member_group,batch=self.batch,module=self.question_module)
        self.batch.start_question=self.question
        self.form_data = {
                        'batch': self.batch,
                        'text': 'whaat?',
                        'answer_type': 'Numerical Answer',
                        'identifier': 'ID 1',
                        'options':"some option text",
                        'group' : self.household_member_group.id,
                        'module' : self.question_module.id
        }

    def test_invalid(self):
        question_form = QuestionForm(self.batch)
        self.assertFalse(question_form.is_valid())

    def test_question_form_fields(self):
        question_form = QuestionForm(self.batch)
        fields = ['module', 'text', 'answer_type', 'group']
        [self.assertIn(field, question_form.fields) for field in fields]

    def test_question_form_has_tuple_of_all_question_modules_as_choices(self):
        health_module = QuestionModule.objects.create(name="Health")
        education_module = QuestionModule.objects.create(name="Education")
        question_modules = [health_module, education_module]
        question_form = QuestionForm(self.batch)
        [self.assertIn((module.id, module.name), question_form.fields['module'].choices) for module in question_modules]

    def test_question_form_has_no_choices_if_there_are_no_question_modules(self):
        QuestionModule.objects.all().delete()
        question_form = QuestionForm(self.batch)
        self.assertEqual(0, len(question_form.fields['module'].choices))

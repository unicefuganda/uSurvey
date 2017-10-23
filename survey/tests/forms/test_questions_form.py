from django.test import TestCase
from survey.forms.question import *
from survey.models import Batch, Survey
from survey.models.questions import Question


class QuestionFormTest(TestCase):

    def setUp(self):
        self.survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        self.question_module = QuestionModule.objects.create(name="Education")
        self.survey = Survey.objects.create(name="Health survey")
        self.batch = Batch.objects.create(name="Health", survey=self.survey)

    def test_question_form_fields(self):
        question_form = QuestionForm()
        fields = ['text', 'answer_type']
        [self.assertIn(field, question_form.fields) for field in fields]

    def test_invalid(self):
        question_form = QuestionForm(self.batch)
        self.assertFalse(question_form.is_valid())


    # def test_question_form_has_tuple_of_all_question_modules_as_choices(self):
    #     health_module = QuestionModule.objects.create(name="Health")
    #     education_module = QuestionModule.objects.create(name="Education")
    #     question_modules = [health_module, education_module]
    #     question_form = QuestionForm(self.batch)
    #     [self.assertIn((module.id, module.name), question_form.fields[
    #                    'module'].choices) for module in question_modules]

    def test_question_form_has_no_choices_if_there_are_no_question_modules(self):
        QuestionModule.objects.all().delete()
        question_form = QuestionForm(self.batch)
        self.assertEqual(1, len(question_form.fields['answer_type'].choices))
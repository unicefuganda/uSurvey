from django.test import TestCase
from survey.forms.question import *
from survey.models import Batch, Survey
from survey.models.questions import Question
from survey.tests.models.survey_base_test import SurveyBaseTest


class QuestionFormTest(SurveyBaseTest):

    def setUp(self):
        super(QuestionFormTest, self).setUp()
        self.survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        self.question_module = QuestionModule.objects.create(name="Education")
        self.survey = Survey.objects.create(name="Health survey")
        self.batch = Batch.objects.create(name="Health", survey=self.survey)

    def test_question_form_fields(self):
        question_form = QuestionForm(self.batch)
        fields = ['text', 'answer_type']
        [self.assertIn(field, question_form.fields) for field in fields]

    def test_invalid(self):
        question_form = QuestionForm(self.batch)
        self.assertFalse(question_form.is_valid())

    def test_question_form_has_no_choices_if_there_are_no_question_modules(self):
        QuestionModule.objects.all().delete()
        question_form = QuestionForm(self.batch)
        self.assertEqual(1, len(question_form.fields['answer_type'].choices))

    def test_attempt_to_use_invalid_placeholder_fails(self):
        self._create_ussd_non_group_questions()
        all_questions = self.qset.all_questions
        data = {'text': 'This {{non_existent}} thing',  'answer_type': NumericalAnswer.choice_name(),
                'identifier': 'testone'}
        question_form = QuestionForm(self.batch, prev_question=all_questions[-1], data=data)
        self.assertFalse(question_form.is_valid())
        self.assertIn('text', question_form.errors)





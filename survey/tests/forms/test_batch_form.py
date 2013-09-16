from django.test import TestCase
from survey.forms.batch import BatchForm, BatchQuestionsForm
from survey.models.question import Question
from survey.models.batch import Batch


class BatchFormTest(TestCase):
    def test_valid(self):
        form_data = {
                        'name': 'Batch 1',
                        'description': 'description goes here',
                    }
        batch_form = BatchForm(form_data)
        self.assertTrue(batch_form.is_valid())

    def test_invalid(self):
        form_data = {
                        'description': 'description goes here',
                    }
        batch_form = BatchForm(form_data)
        self.assertFalse(batch_form.is_valid())

    def test_form_should_be_invalid_if_name_already_exists(self):
        Batch.objects.create(name='Batch A',description='description')
        form_data = {
                        'name': 'Batch A',
                        'description': 'description goes here',
                    }
        batch_form = BatchForm(form_data)
        self.assertFalse(batch_form.is_valid())
        self.assertIn('Batch with the same name already exist', batch_form.errors['name'])

class BatchQuestionsFormTest(TestCase):
    def setUp(self):
        self.q1=Question.objects.create(text="question1", answer_type=Question.NUMBER)
        self.q2=Question.objects.create(text="question2", answer_type=Question.TEXT)
        self.form_data = {
                    'questions': [self.q1.id, self.q2.id],
                }

    def test_valid(self):
        batch_questions_form = BatchQuestionsForm(self.form_data)
        self.assertTrue(batch_questions_form.is_valid())

    def test_invalid(self):
        some_question_id_that_does_not_exist = 1234
        form_data = {
                        'questions': some_question_id_that_does_not_exist
                    }
        batch_questions_form = BatchQuestionsForm(form_data)
        self.assertFalse(batch_questions_form.is_valid())
        message = 'Enter a list of values.'
        self.assertEquals([message], batch_questions_form.errors['questions'])
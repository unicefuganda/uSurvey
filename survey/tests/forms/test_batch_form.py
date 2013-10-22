from django.test import TestCase
from survey.forms.batch import BatchForm, BatchQuestionsForm
from survey.models import BatchQuestionOrder
from survey.models.question import Question
from survey.models.batch import Batch
from survey.models.surveys import Survey

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

    def test_form_should_be_invalid_if_name_already_exists_on_the_same_survey(self):
        survey = Survey.objects.create(name="very fast")
        Batch.objects.create(survey=survey, name='Batch A',description='description')
        form_data = {
                        'name': 'Batch A',
                        'description': 'description goes here',
                    }
        batch_form = BatchForm(data=form_data, instance= Batch(survey=survey))
        self.assertFalse(batch_form.is_valid())
        self.assertIn('Batch with the same name already exists.', batch_form.errors['name'])

    def test_form_should_be_valid_if_name_already_exists_on_a_different_survey(self):
        survey = Survey.objects.create(name="very fast")
        form_data = {
                        'name': 'Batch A',
                        'description': 'description goes here',
                    }

        Batch.objects.create(survey=survey, name=form_data['name'], description='description')
        different_survey = Survey.objects.create(name="different")
        batch_form = BatchForm(data=form_data, instance= Batch(survey=different_survey))
        self.assertTrue(batch_form.is_valid())


class BatchQuestionsFormTest(TestCase):

    def setUp(self):
        self.q1=Question.objects.create(text="question1", answer_type=Question.NUMBER)
        self.q2=Question.objects.create(text="question2", answer_type=Question.TEXT)
        self.form_data = {
                'questions': [self.q1.id, self.q2.id],
                }
        self.batch = Batch.objects.create(name="Batch A", order=2)
        self.batch_questions_form = BatchQuestionsForm(batch=self.batch, data=self.form_data, instance=self.batch)

    def test_valid(self):
        self.assertTrue(self.batch_questions_form.is_valid())

    def test_invalid(self):
        some_question_id_that_does_not_exist = 1234
        form_data = {
                        'questions': some_question_id_that_does_not_exist
                    }
        batch_questions_form = BatchQuestionsForm(batch=self.batch, data=form_data)
        self.assertFalse(batch_questions_form.is_valid())
        message = 'Enter a list of values.'
        self.assertEquals([message], batch_questions_form.errors['questions'])

    def test_has_only_questions_not_subquestions_in_the_form(self):
        question1 = Question.objects.create(text="question1", answer_type=Question.NUMBER)
        question2 = Question.objects.create(text="question2", answer_type=Question.TEXT)
        sub_question1 = Question.objects.create(text="sub-question1", answer_type=Question.TEXT, parent=question1, subquestion=True)
        batch_form = BatchQuestionsForm(batch=self.batch)

        question_choices = batch_form.fields['questions']._queryset
        self.assertIn(question1, question_choices)
        self.assertIn(question2, question_choices)

        self.assertNotIn(sub_question1, question_choices)

    def test_should_save_order_when_form_save_is_called_with_questions(self):
        self.batch_questions_form.save()

        self.assertIn(self.batch, self.q1.batches.all())
        self.assertIn(self.batch, self.q2.batches.all())
        all_batch_question_orders = BatchQuestionOrder.objects.all()
        self.assertEqual(2, len(all_batch_question_orders))
        self.assertIsNotNone(self.q1.question_batch_order.all())
        self.assertIsNotNone(self.q2.question_batch_order.all())

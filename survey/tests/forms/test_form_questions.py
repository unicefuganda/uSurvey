from django.test import TestCase
from survey.forms.question import *
from survey.models import *

class QuestionFormTest(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(name='Batch A',description='description')
        self.form_data = {
                        'batch': self.batch.id,
                        'text': 'whaat?',
                        'answer_type': Question.NUMBER,
        }


    def test_valid(self):
        question_form = QuestionForm(self.form_data)
        question_form.is_valid()
        self.assertTrue(question_form.is_valid())


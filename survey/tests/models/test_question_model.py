
from django.test import TestCase
from survey.models import QuestionModule
from django.db import IntegrityError
from survey.models.batch import Batch
from survey.models.questions import Question, QuestionOption


class QuestionTest(TestCase):

    def setUp(self):
        self.question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        self.batch = Batch.objects.create(order=1)

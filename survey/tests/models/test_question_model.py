
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

    def test_fields(self):
        ss_content = Question()
        fields = [str(item.attname) for item in ss_content._meta.fields]
        self.assertEqual(9, len(fields))
        for field in ['id','created','modified','identifier','text','answer_type','mandatory','qset_id','response_validation_id']:
            self.assertIn(field, fields)

        s_content = QuestionOption()
        fields = [str(item.attname) for item in s_content._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created', 'modified', 'question_id', 'text', 'order']:
            self.assertIn(field, fields)

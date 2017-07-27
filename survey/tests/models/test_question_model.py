
from django.test import TestCase
from survey.models import QuestionModule
from django.db import IntegrityError
from survey.models.batch import Batch
from survey.models.questions import Question, QuestionOption, QuestionSet


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
class QuestionOptionTest(TestCase):
    def test_unicode_text(self):
        opt = QuestionOption.objects.create(text="module name")
        self.assertEqual(opt.text, str(opt))
class QuestionSetTest(TestCase):
    def test_unicode_text(self):
        qst = QuestionSet.objects.create(name="module name")
        self.assertEqual(qst.name, str(qst))
from django.test import TestCase
from survey.models import EnumerationArea,SurveyAllocation

from survey.models.batch import Batch
from survey.models.interviewer import Interviewer
from survey.models.surveys import Survey,SurveyAllocation
from survey.models.questions import Question, QuestionOption
from survey.models.question_module import QuestionModule


class InterviewerTest(TestCase):

    def test_fields(self):
        ss_content = Interviewer()
        fields = [str(item.attname) for item in ss_content._meta.fields]
        self.assertEqual(11, len(fields))
        for field in ['id','created','modified','name','gender','date_of_birth','level_of_education','is_blocked','ea_id','language','weights']:
            self.assertIn(field, fields)

    def test_store(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        batch = Batch.objects.create(order=1)
        self.failUnless(batch.id)
        self.failUnless(ea.id)
        self.failUnless(survey.id)

    def setUp(self):
        Interviewer.objects.create(name="Dummy")

    def test_name(self):
        name = Interviewer.objects.get(name="Dummy")
        self.assertEqual(name.name,'Dummy')
        self.assertEqual(len(name.name),5)
    def test_unicode_text(self):
        itr = Interviewer.objects.create(name="abcd name")
        self.assertEqual(itr.name, str(itr))
class SurveyAllocationTest(TestCase):

    def test_unicode_text(self):
        sua = SurveyAllocation.objects.create(allocation_ea="abcd name")
        self.assertEqual(sua.allocation_ea.name, str(sua))
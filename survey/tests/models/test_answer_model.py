from django.test import TestCase
from survey.models import EnumerationArea

from survey.models.batch import Batch
from survey.models.interviewer import Interviewer
from survey.models.surveys import Survey
from survey.models.questions import Question, QuestionOption
from survey.models.question_module import QuestionModule
from survey.models.interviews import NumericalAnswer, TextAnswer, MultiChoiceAnswer, Interview
from survey.models.access_channels import InterviewerAccess, ODKAccess


class NumericalAnswerTest(TestCase):

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


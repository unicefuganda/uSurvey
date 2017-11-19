import string
from model_mommy import mommy
from datetime import datetime
from django.utils import timezone
from dateutil.parser import parse as extract_date
from django.conf import settings
from survey.models import (InterviewerAccess, ODKAccess, USSDAccess, Interview, Interviewer, QuestionSetChannel,
                           EnumerationArea, Survey, SurveyAllocation, Question, QuestionSet, Batch, BatchQuestion,
                           QuestionOption)
from survey.forms.question import get_question_form
from .survey_base_test import SurveyBaseTest
from survey.tests.base_test import BaseTest
# import all question types
from survey.models import (Answer, NumericalAnswer, TextAnswer, MultiChoiceAnswer, MultiSelectAnswer, GeopointAnswer,
                           ImageAnswer, AudioAnswer, VideoAnswer, DateAnswer, AutoResponse, ListingTemplate)


class QuestionModelTest(SurveyBaseTest):

    def setUp(self):
        super(QuestionModelTest, self).setUp()
        self.listing_form = mommy.make(ListingTemplate)
        self.listing_question = mommy.make(Question, qset=self.listing_form)
        self.sampling_survey = mommy.make(Survey, listing_form=self.listing_form, has_sampling=True, name='sample test survey')
        self.batch = mommy.make(Batch, survey=self.sampling_survey)
        # self.parameter_question =

    def test_get_question_brings_correct_question_type(self):
        self.assertEquals(QuestionSet.get(pk=self.batch.pk).__class__, Batch)

 #   def test_e_qset_gets_correct_questionset_type(self):
 #       self.assertEquals(self.batch_question.e_qset.__class__, Batch)
 #       self.assertEquals(self.listing_question.e_qset.__class__, ListingTemplate)

    # def test_





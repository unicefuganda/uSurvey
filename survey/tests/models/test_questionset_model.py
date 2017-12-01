__author__ = 'antsmc2'
import time
from django.core.files.uploadedfile import SimpleUploadedFile
from lxml import etree
import python_digest
from model_mommy import mommy
import random
from hashlib import md5
from django.test import TestCase
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.contrib.auth.models import User
from survey.models import (InterviewerAccess, ODKAccess, USSDAccess, Interview, Interviewer, QuestionSetChannel,
                           EnumerationArea, Survey, SurveyAllocation, Question, QuestionSet, Batch, BatchQuestion,
                           QuestionOption, ODKSubmission)
from survey.forms.question import get_question_form
# import all question types
from survey.models import (Answer, NumericalAnswer, TextAnswer, MultiChoiceAnswer, MultiSelectAnswer, GeopointAnswer,
                           ImageAnswer, AudioAnswer, VideoAnswer, DateAnswer, AutoResponse)
from survey.tests.models.survey_base_test import SurveyBaseTest


class QuestionSetTest(SurveyBaseTest):

    def test_clone_questionset(self):
        self._create_ussd_non_group_questions()
        self.assertEquals(QuestionSet.objects.filter(name__icontains=self.qset.name).count(), 1)
        self.assertEquals(Question.objects.filter(qset=self.qset).count(), 4)
        self.qset.deep_clone()
        # now check if the questions has increased
        self.assertEquals(Question.objects.filter(qset__name__icontains=self.qset.name).count(), 8)
        self.assertEquals(QuestionSet.objects.filter(name__icontains=self.qset.name).count(), 2)
        self.assertEquals(QuestionSetChannel.objects.filter(qset__id=self.qset.id).count(),
                          QuestionSetChannel.objects.exclude(qset__id=self.qset.id
                                                             ).filter(qset__name__icontains=self.qset.name).count())

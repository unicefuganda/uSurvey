import string
from datetime import datetime
from django_rq import job
from django.contrib.auth.models import User
from django.utils import timezone
from dateutil.parser import parse as extract_date
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from survey.models.base import BaseModel
from survey.models.access_channels import InterviewerAccess, ODKAccess, USSDAccess
from survey.models.locations import Point
from survey.utils.decorators import static_var
from survey.models.interviews import Interview
from django.test import TestCase

def test_fields(self):
    interview = Interview()
    fields = [str(item.attname) for item in interview._meta.fields]
    self.assertEqual(13, len(fields))
    for field in ['id','created','modified','closure_date','test_data','ea_id','interview_channel_id','interview_reference_id','interviewer_id','last_question_id','question_set_id','survey_id','uploaded_by_id']:
        self.assertIn(field, fields)

def test_store(self):
    interview = Interview.objects.create(test_data="True",ea_id=1,interview_channel_id=1,interview_reference_id=1,interviewer_id=1,last_question_id=1,question_set_id=1,survey_id=1,uploaded_by_id=1)
    self.failUnless(interview.id)
    self.failUnless(interview.created)
    self.failUnless(interview.test_data)
    self.failUnless(interview.ea_id)
    self.failUnless(interview.interview_channel_id)
    self.failUnless(interview.interview_reference_id)
    self.failUnless(interview.interviewer_id)
    self.failUnless(interview.last_question_id)
    self.failUnless(interview.question_set_id)
    self.failUnless(interview.survey_id)
    self.failUnless(interview.uploaded_by_id)
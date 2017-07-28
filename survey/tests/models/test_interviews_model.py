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

class InterviewTest(TestCase):

    def test_unicode_text(self):
        sua = Interview.objects.create(name="abcd name")
        self.assertEqual(sua.name, str(sua))
from django.test import TestCase
from survey.models import *
from django.db import IntegrityError


class InvestigatorTest(TestCase):

    def test_store(self):
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210")
        self.failUnless(investigator.id)
        self.failUnless(investigator.created)
        self.failUnless(investigator.modified)

    def test_validations(self):
        Investigator.objects.create(name="", mobile_number = "mobile_number")
        self.failUnlessRaises(IntegrityError, Investigator.objects.create, mobile_number = "mobile_number")
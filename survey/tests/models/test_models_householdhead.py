from django.test import TestCase
from survey.models import *
from django.db import IntegrityError, DatabaseError
from rapidsms.contrib.locations.models import Location, LocationType

class HouseholdHeadTest(TestCase):

    def test_fields(self):
        hHead = HouseholdHead()
        fields = [str(item.attname) for item in hHead._meta.fields]
        self.assertEqual(len(fields), 11)
        for field in ['id', 'surname', 'first_name', 'created', 'modified', 'male', 'age', 'level_of_education', 'resident_since', 'household_id']:
            self.assertIn(field, fields)

    def test_store(self):
        hHead = HouseholdHead.objects.create(surname="Daddy")
        self.failUnless(hHead.id)
        self.failUnless(hHead.created)
        self.failUnless(hHead.modified)
        self.assertEquals(0, hHead.resident_since)


from django.test import TestCase
from survey.models import *
from django.db import IntegrityError, DatabaseError
from rapidsms.contrib.locations.models import Location, LocationType

class HouseholdTest(TestCase):

    def test_fields(self):
        hHead = HouseHold()
        fields = [str(item.attname) for item in hHead._meta.fields]
        self.assertEqual(len(fields), 15)
        for field in ['id', 'head_id', 'investigator_id', 'created', 'modified', 'number_of_males', 'number_of_females',
                      'children_5_12_years', 'children_13_17_years', 'children_0_5_months', 'children_6_11_months',
                      'children_12_23_months', 'children_24_59_months', 'women_15_19_years', 'women_20_49_years']:
            self.assertIn(field, fields)

    def test_store(self):
        hhold = HouseHold.objects.create(investigator=Investigator(), head=HouseholdHead())
        self.failUnless(hhold.id)
        self.failUnless(hhold.created)
        self.failUnless(hhold.modified)
        self.assertEquals(0, hhold.number_of_males)
        self.assertEquals(0, hhold.number_of_females)
        self.assertEquals(0, hhold.children_5_12_years)
        self.assertEquals(0, hhold.children_13_17_years)
        self.assertEquals(0, hhold.children_0_5_months)
        self.assertEquals(0, hhold.children_6_11_months)
        self.assertEquals(0, hhold.children_12_23_months)
        self.assertEquals(0, hhold.children_24_59_months)
        self.assertEquals(0, hhold.women_15_19_years)
        self.assertEquals(0, hhold.women_20_49_years)




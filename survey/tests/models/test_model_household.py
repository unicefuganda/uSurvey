from django.test import TestCase
from survey.models import *

class HouseholdTest(TestCase):

    def test_fields(self):
        hHead = HouseHold()
        fields = [str(item.attname) for item in hHead._meta.fields]
        self.assertEqual(len(fields), 6)
        for field in ['id', 'investigator_id', 'created', 'modified', 'number_of_males', 'number_of_females']:
            self.assertIn(field, fields)

    def test_store(self):
        hhold = HouseHold.objects.create(investigator=Investigator())
        self.failUnless(hhold.id)
        self.failUnless(hhold.created)
        self.failUnless(hhold.modified)
        self.assertEquals(0, hhold.number_of_males)
        self.assertEquals(0, hhold.number_of_females)




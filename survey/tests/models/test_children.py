from django.test import TestCase
from survey.models import *

class ChildrenTest(TestCase):

    def test_fields(self):
        children = Children()
        fields = [str(item.attname) for item in children._meta.fields]
        self.assertEqual(len(fields), 10)
        for field in ['id', 'household_id', 'created', 'modified', 'aged_between_5_12_years', 'aged_between_13_17_years',
                    'aged_between_0_5_months',  'aged_between_6_11_months', 'aged_between_12_23_months', 'aged_between_24_59_months']:
            self.assertIn(field, fields)

    def test_store(self):
        children = Children.objects.create(household=HouseHold())
        self.failUnless(children.id)
        self.failUnless(children.created)
        self.failUnless(children.modified)
        self.assertEquals(0, children.aged_between_5_12_years)
        self.assertEquals(0, children.aged_between_13_17_years)
        self.assertEquals(0, children.aged_between_0_5_months)
        self.assertEquals(0, children.aged_between_6_11_months)
        self.assertEquals(0, children.aged_between_12_23_months)
        self.assertEquals(0, children.aged_between_24_59_months)


from django.test import TestCase
from survey.models_file import *

class ChildrenTest(TestCase):

    def test_fields(self):
        ladies = Women()
        fields = [str(item.attname) for item in ladies._meta.fields]
        self.assertEqual(len(fields), 6)
        for field in ['id', 'household_id', 'created', 'modified', 'aged_between_15_19_years', 'aged_between_20_49_years']:
            self.assertIn(field, fields)

    def test_store(self):
        ladies = Women.objects.create(household=Household())
        self.failUnless(ladies.id)
        self.failUnless(ladies.created)
        self.failUnless(ladies.modified)
        self.assertEquals(0, ladies.aged_between_15_19_years)
        self.assertEquals(0, ladies.aged_between_20_49_years)


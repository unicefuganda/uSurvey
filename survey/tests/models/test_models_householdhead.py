from django.test import TestCase
from survey.models.households import HouseholdHead


class HouseholdHeadTest(TestCase):

    def test_fields(self):
        hHead = HouseholdHead()
        fields = [str(item.attname) for item in hHead._meta.fields]
        self.assertEqual(len(fields), 12)
        for field in ['id', 'surname', 'first_name', 'created', 'modified', 'male', 'age', 'occupation',
                        'level_of_education', 'resident_since_year', 'resident_since_month', 'household_id']:
            self.assertIn(field, fields)

    def test_store(self):
        hHead = HouseholdHead.objects.create(surname="Daddy")
        self.failUnless(hHead.id)
        self.failUnless(hHead.created)
        self.failUnless(hHead.modified)
        self.assertEquals(1984, hHead.resident_since_year)
        self.assertEquals(5, hHead.resident_since_month)

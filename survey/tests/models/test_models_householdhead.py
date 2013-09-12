from datetime import date
from django.test import TestCase
from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Investigator, Backend
from survey.models.households import HouseholdHead, Household


class HouseholdHeadTest(TestCase):

    def test_fields(self):
        hHead = HouseholdHead()
        fields = [str(item.attname) for item in hHead._meta.fields]
        self.assertEqual(len(fields), 13)
        for field in ['id', 'surname', 'first_name', 'created', 'modified', 'male', 'occupation', 'date_of_birth',
                        'level_of_education', 'resident_since_year', 'resident_since_month', 'household_id']:
            self.assertIn(field, fields)

    def test_store(self):
        village = LocationType.objects.create(name="Village", slug=slugify("village"))
        some_village = Location.objects.create(name="Some village", type=village)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))
        household = Household.objects.create(investigator=investigator, uid=0)

        hHead = HouseholdHead.objects.create(surname="Daddy", date_of_birth=date(1980, 05, 01), household=household)
        self.failUnless(hHead.id)
        self.failUnless(hHead.created)
        self.failUnless(hHead.modified)
        self.assertEquals(1984, hHead.resident_since_year)
        self.assertEquals(5, hHead.resident_since_month)
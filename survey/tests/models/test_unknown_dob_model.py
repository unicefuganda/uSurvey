from datetime import date
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Investigator, Household, Backend
from survey.models.households import HouseholdMember
from survey.models.unknown_dob_attribute import UnknownDOBAttribute
from survey.tests.base_test import BaseTest


class UnknownDOBAttributeTest(BaseTest):
    def test_fields(self):
        unknown_dob = UnknownDOBAttribute()
        fields = [str(item.attname) for item in unknown_dob._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'household_member_id', 'type']:
            self.assertIn(field, fields)

    def test_store(self):
        village = LocationType.objects.create(name="Village", slug="village")
        some_village = Location.objects.create(name="Some village", type=village)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321",
                                                   location=some_village,
                                                   backend=Backend.objects.create(name='something1'))
        household = Household.objects.create(investigator=investigator, uid=0)
        fields_data = dict(surname='xyz', male=True, date_of_birth=date(1980, 05, 01), household=household)
        household_member = HouseholdMember.objects.create(**fields_data)

        unknown_dob = UnknownDOBAttribute.objects.create(household_member=household_member, type="MONTH" )

        self.failUnless(unknown_dob.id)

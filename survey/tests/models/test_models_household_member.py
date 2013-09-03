from datetime import date
from django.template.defaultfilters import slugify
from django.test import TestCase
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import HouseholdMember, Household, Investigator, Backend


class HouseholdMemberTest(TestCase):
    def test_should_have_fields_required(self):
        household_member = HouseholdMember()
        fields = [str(item.attname) for item in household_member._meta.fields]

        field_list_expected = ['name', 'male', 'date_of_birth', 'household_id']

        [self.assertIn(field_expected, fields) for field_expected in field_list_expected]

    def test_should_validate_household_member_belongs_to_household(self):
        village = LocationType.objects.create(name="Village", slug=slugify("village"))
        some_village = Location.objects.create(name="Some village", type=village)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))
        household = Household.objects.create(investigator=investigator, uid=0)
        fields_data = dict(name='xyz', male=True, date_of_birth=date(1980, 05, 01), household=household)
        household_member = HouseholdMember.objects.create(**fields_data)
        self.failUnless(household_member)
        self.assertEqual(household_member.name, fields_data['name'])
        self.assertTrue(household_member.male)
        self.assertEqual(household_member.date_of_birth, fields_data['date_of_birth'])
        self.assertEqual(household_member.household, household)


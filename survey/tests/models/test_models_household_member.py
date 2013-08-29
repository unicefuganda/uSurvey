from datetime import date
from django.test import TestCase
from survey.models import HouseholdMember


class HouseholdMemberTest(TestCase):
    def test_should_have_fields_required(self):
        household_member = HouseholdMember()
        fields = [str(item.attname) for item in household_member._meta.fields]

        field_list_expected = ['name', 'male', 'date_of_birth']

        [self.assertIn(field_expected, fields) for field_expected in field_list_expected]

    def test_should_validate_household_member_fields(self):
        fields_data = dict(name='xyz', male=True, date_of_birth=date(1980, 05, 01))
        household_member = HouseholdMember.objects.create(**fields_data)
        self.failUnless(household_member)
        self.assertEqual(household_member.name, fields_data['name'])
        self.assertTrue(household_member.male)
        self.assertEqual(household_member.date_of_birth, fields_data['date_of_birth'])

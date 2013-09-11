from datetime import date
from django.template.defaultfilters import slugify
from django.test import TestCase
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition
from survey.models.households import HouseholdMember, Household, HouseholdHead
from survey.models.backend import Backend
from survey.models.investigator import Investigator

class HouseholdMemberTest(TestCase):
    def test_should_have_fields_required(self):
        household_member = HouseholdMember()
        fields = [str(item.attname) for item in household_member._meta.fields]

        field_list_expected = ['surname', 'first_name', 'male', 'date_of_birth', 'household_id']

        [self.assertIn(field_expected, fields) for field_expected in field_list_expected]

    def test_should_validate_household_member_belongs_to_household(self):
        village = LocationType.objects.create(name="Village", slug=slugify("village"))
        some_village = Location.objects.create(name="Some village", type=village)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))
        household = Household.objects.create(investigator=investigator, uid=0)
        fields_data = dict(surname='xyz', male=True, date_of_birth=date(1980, 05, 01), household=household)
        household_member = HouseholdMember.objects.create(**fields_data)
        self.failUnless(household_member)
        self.assertEqual(household_member.surname, fields_data['surname'])
        self.assertTrue(household_member.male)
        self.assertEqual(household_member.date_of_birth, fields_data['date_of_birth'])
        self.assertEqual(household_member.household, household)

    def test_household_member_knows_age(self):
        village = LocationType.objects.create(name="Village", slug=slugify("village"))
        some_village = Location.objects.create(name="Some village", type=village)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))
        household = Household.objects.create(investigator=investigator, uid=0)
        fields_data = dict(surname='xyz', male=True, date_of_birth=date(1980, 05, 01), household=household)
        household_member = HouseholdMember.objects.create(**fields_data)

        self.assertEqual(household_member.get_age(), 33)

    def test_household_member_should_know_groups_they_belong_to(self):
        age_value = 6
        age_attribute_type = "Age"
        gender_attribute_type = "Male"

        village = LocationType.objects.create(name="Village", slug=slugify("village"))
        some_village = Location.objects.create(name="Some village", type=village)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))
        household = Household.objects.create(investigator=investigator, uid=0)
        fields_data = dict(surname='xyz', male=True, date_of_birth=date(2013, 05, 01), household=household)
        household_member = HouseholdMember.objects.create(**fields_data)

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        another_member_group = HouseholdMemberGroup.objects.create(name="7 to 10 years", order=1)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value, condition='LESS_THAN')
        age_condition.groups.add(member_group)

        another_age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=7, condition='GREATER_THAN')
        another_age_condition.groups.add(another_member_group)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True, condition='EQUALS')
        gender_condition.groups.add(member_group)

        member_groups = household_member.get_member_groups()
        self.assertEqual(len(member_groups), 1)
        self.assertIn(member_group, member_groups)
        self.assertNotIn(another_member_group, member_groups)

    def test_household_member_is_head(self):
        hhold = Household.objects.create(investigator=Investigator(), uid=0)
        household_head = HouseholdHead.objects.create(household=hhold, surname="Name", date_of_birth='1989-02-02')
        household_member = HouseholdMember.objects.create(household=hhold, surname="name", male=False, date_of_birth='1989-02-02')

        self.assertTrue(household_head.is_head())
        self.assertFalse(household_member.is_head())
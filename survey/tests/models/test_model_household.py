from django.template.defaultfilters import slugify
from datetime import date
from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import HouseholdMemberGroup, GroupCondition, Question, Batch, HouseholdBatchCompletion
from survey.models.households import Household, HouseholdHead, HouseholdMember
from survey.models.backend import Backend
from survey.models.investigator import Investigator



class HouseholdTest(TestCase):

    def test_fields(self):
        hHead = Household()
        fields = [str(item.attname) for item in hHead._meta.fields]
        self.assertEqual(len(fields), 5)
        for field in ['id', 'investigator_id', 'created', 'modified', 'uid']:
            self.assertIn(field, fields)

    def test_store(self):
        hhold = Household.objects.create(investigator=Investigator(), uid=0)
        self.failUnless(hhold.id)
        self.failUnless(hhold.created)
        self.failUnless(hhold.modified)
        self.assertEquals(0, hhold.uid)

    def test_should_know_household_related_location_to_village_level(self):
        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        county = LocationType.objects.create(name="County", slug=slugify("county"))
        sub_county = LocationType.objects.create(name="Subcounty", slug=slugify("sub-county"))
        parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
        village = LocationType.objects.create(name="Village", slug=slugify("village"))

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala_district = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto_county = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala_district)
        some_sub_county = Location.objects.create(name="Some sub county", type=sub_county, tree_parent=bukoto_county)
        some_parish = Location.objects.create(name="Some parish", type=parish, tree_parent=some_sub_county)
        some_village = Location.objects.create(name="Some village", type=village, tree_parent=some_parish)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1 , uid=0)
        household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county', 'Parish': 'Some parish', 'Village': 'Some village'}

        self.assertEqual(household_location, household1.get_related_location())

    def test_should_know_how_to_set_household_location_given_a_set_of_households(self):
        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        county = LocationType.objects.create(name="County", slug=slugify("county"))
        sub_county = LocationType.objects.create(name="Subcounty", slug=slugify("sub-county"))
        parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
        village = LocationType.objects.create(name="Village", slug=slugify("village"))

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala_district = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto_county = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala_district)
        some_sub_county = Location.objects.create(name="Some sub county", type=sub_county, tree_parent=bukoto_county)
        some_parish = Location.objects.create(name="Some parish", type=parish, tree_parent=some_sub_county)
        some_village = Location.objects.create(name="Some village", type=village, tree_parent=some_parish)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1, uid=0)
        household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county', 'Parish': 'Some parish', 'Village': 'Some village'}

        households = Household.set_related_locations([household1])

        self.assertEqual(household_location, households[0].related_locations)

    def test_get_location_for_some_hierarchy_returns_the_name_if_key_exists_in_location_hierarchy_dict(self):
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        kampala_district = Location.objects.create(name="Kampala", type=district)
        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=kampala_district, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1, uid=0)

        location_hierarchy = {'District': kampala_district}

        self.assertEqual(household1._get_related_location_name('District', location_hierarchy), kampala_district.name)

    def test_get_location_for_some_hierarchy_returns_empty_string_if_key_does_not_exist_in_location_hierarchy_dict(self):
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        kampala_district = Location.objects.create(name="Kampala", type=district)
        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=kampala_district, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1, uid=0)

        location_hierarchy = {'District': kampala_district}

        self.assertEqual(household1._get_related_location_name('County', location_hierarchy), "")

    def test_should_know_how_to_get_household_location_for_a_single_household(self):
        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        county = LocationType.objects.create(name="County", slug=slugify("county"))
        sub_county = LocationType.objects.create(name="Subcounty", slug=slugify("sub-county"))
        parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
        village = LocationType.objects.create(name="Village", slug=slugify("village"))

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala_district = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto_county = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala_district)
        some_sub_county = Location.objects.create(name="Some sub county", type=sub_county, tree_parent=bukoto_county)
        some_parish = Location.objects.create(name="Some parish", type=parish, tree_parent=some_sub_county)
        some_village = Location.objects.create(name="Some village", type=village, tree_parent=some_parish)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1, uid=0)
        household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county', 'Parish': 'Some parish', 'Village': 'Some village'}

        self.assertEqual(household_location, household1.get_related_location())

    def test_should_know_who_is_household_head(self):
        village = LocationType.objects.create(name="Village", slug=slugify("village"))
        some_village = Location.objects.create(name="Some village", type=village)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))
        household = Household.objects.create(investigator=investigator, uid=0)
        fields_data = dict(surname='xyz', male=True, date_of_birth=date(2013, 05, 01), household=household)

        hHead = HouseholdHead.objects.create(surname="Daddy", date_of_birth=date(1980, 05, 01), household=household)
        household_member = HouseholdMember.objects.create(**fields_data)

        self.assertEqual(hHead, household.get_head())
        self.assertNotEqual(household_member, household.get_head())


    def test_should_return_all_households_members(self):
        hhold = Household.objects.create(investigator=Investigator(), uid=0)
        household_head = HouseholdHead.objects.create(household=hhold,surname="Name", date_of_birth='1989-02-02')
        household_member1 = HouseholdMember.objects.create(household=hhold, surname="name", male=False, date_of_birth='1989-02-02')
        household_member2 = HouseholdMember.objects.create(household=hhold, surname="name1", male=False, date_of_birth='1989-02-02')
        all_members = hhold.all_members()
        self.assertTrue(household_head in all_members)
        self.assertTrue(household_member1 in all_members)
        self.assertTrue(household_member2 in all_members)

    def test_should_know_if_all_members_have_completed_currently_open_batches(self):
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                   location=kampala,
                                                   backend=backend)
        hhold = Household.objects.create(investigator=investigator, uid=0)
        household_head = HouseholdHead.objects.create(household=hhold,surname="Name", date_of_birth=date(1989, 2, 2))
        household_member1 = HouseholdMember.objects.create(household=hhold, surname="name2", male=False, date_of_birth=date(1989, 2, 2))
        household_member2 = HouseholdMember.objects.create(household=hhold, surname="name3", male=False, date_of_birth=date(1989, 2, 2))
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        condition.groups.add(member_group)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch_2 = Batch.objects.create(name="BATCH B", order=2)

        batch.open_for_location(investigator.location)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group, batch=batch)

        member_list = [household_head, household_member1, household_member2]

        self.assertFalse(hhold.completed_currently_open_batches())
        investigator.member_answered(question_1, household_member1, answer=1)
        self.assertFalse(hhold.completed_currently_open_batches())
        investigator.member_answered(question_1, household_member2, answer=1)
        self.assertFalse(hhold.completed_currently_open_batches())
        investigator.member_answered(question_1, household_head, answer=1)
        self.assertTrue(hhold.completed_currently_open_batches())
        self.assertEqual(3, HouseholdBatchCompletion.objects.filter(batch=batch).count())
        [self.assertEqual(1, HouseholdBatchCompletion.objects.filter(batch=batch, householdmember=member).count()) for member in member_list]

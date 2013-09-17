from datetime import date
from django.template.defaultfilters import slugify
from django.test import TestCase
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import Batch, Question
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
        age_attribute_type = "AGE"
        gender_attribute_type = "GENDER"

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

    def test_household_member_knows_location(self):
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
        hhold = Household.objects.create(investigator=investigator1, uid=0)
        household_member = HouseholdMember.objects.create(household=hhold, surname="name", male=True, date_of_birth=date(1998, 2, 2))

        self.assertEqual(investigator1.location, household_member.get_location())

    def test_member_gets_the_question_that_belongs_to_his_group(self):
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

        self.batch = Batch.objects.create(name="Batch 1", order=1)
        group = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
        group_condition = GroupCondition.objects.create(attribute="GENDER", condition="EQUALS", value=True)
        group_condition.groups.add(group)

        question_1 = Question.objects.create(batch=self.batch, group=group, text="This is another question", answer_type="number", order=1)
        question_2 = Question.objects.create(batch=self.batch, group=group, text="This is a question", answer_type="number", order=2)

        self.batch.open_for_location(uganda)

        hhold = Household.objects.create(investigator=investigator1, uid=0)
        household_member = HouseholdMember.objects.create(household=hhold, surname="name", male=True, date_of_birth=date(1998, 2, 2))

        self.assertEqual(question_1, household_member.next_question())

    def test_gets_next_group_with_un_answered_questions(self):
        country = LocationType.objects.create(name="Country", slug="country")
        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        less_condition = GroupCondition.objects.create(attribute="age", condition="GREATER_THAN", value=4)
        greater_condition = GroupCondition.objects.create(attribute="age", condition="LESS_THAN", value=6)
        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        less_condition.groups.add(member_group)
        greater_condition.groups.add(member_group)

        female_group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        female_condition = GroupCondition.objects.create(attribute="gender", condition="EQUALS", value=False)
        female_condition.groups.add(female_group)

        batch = Batch.objects.create(name="BATCH A", order=1)
        household = Household.objects.create(investigator=investigator, uid=0)

        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2008, 8, 30)),
                                                          male=False,
                                                          household=household)
        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group, batch=batch)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group, batch=batch)

        question_3 = Question.objects.create(identifier="identifier1", text="Question 3",
                                             answer_type='number', order=1,
                                             subquestion=False, group=female_group, batch=batch)
        investigator.member_answered(question=question_1, household_member=household_member, answer=1)
        investigator.member_answered(question=question_2, household_member=household_member, answer=1)
        self.assertEqual(female_group, household_member.get_next_group())

    def test_knows_how_to_get_the_next_questions_from_the_next_group(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        less_condition = GroupCondition.objects.create(attribute="age", condition="GREATER_THAN", value=4)
        greater_condition = GroupCondition.objects.create(attribute="age", condition="LESS_THAN", value=6)
        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        less_condition.groups.add(member_group)
        greater_condition.groups.add(member_group)

        female_group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        female_condition = GroupCondition.objects.create(attribute="gender", condition="EQUALS", value=False)
        female_condition.groups.add(female_group)

        batch = Batch.objects.create(name="BATCH A", order=1)
        batch.open_for_location(investigator.location)
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2008, 8, 30)),
                                                          male=False,
                                                          household=household)
        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group, batch=batch)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group, batch=batch)

        question_3 = Question.objects.create(identifier="identifier1", text="Question 3",
                                             answer_type='number', order=1,
                                             subquestion=False, group=female_group, batch=batch)

        self.assertEqual(question_1, household_member.next_question())
        investigator.member_answered(question=question_1, household_member=household_member, answer=1)
        self.assertEqual(question_2, household_member.next_question())
        investigator.member_answered(question=question_2, household_member=household_member, answer=1)
        self.assertEqual(question_3, household_member.next_question())

    def test_knows_all_questions_are_answered(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        less_condition = GroupCondition.objects.create(attribute="age", condition="GREATER_THAN", value=4)
        greater_condition = GroupCondition.objects.create(attribute="age", condition="LESS_THAN", value=6)
        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        less_condition.groups.add(member_group)
        greater_condition.groups.add(member_group)

        female_group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        female_condition = GroupCondition.objects.create(attribute="gender", condition="EQUALS", value=False)
        female_condition.groups.add(female_group)

        batch = Batch.objects.create(name="BATCH A", order=1)
        batch.open_for_location(investigator.location)

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2008, 8, 30)),
                                                          male=False,
                                                          household=household)
        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group, batch=batch)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group, batch=batch)

        question_3 = Question.objects.create(identifier="identifier1", text="Question 3",
                                             answer_type='number', order=1,
                                             subquestion=False, group=female_group, batch=batch)

        investigator.member_answered(question=question_1, household_member=household_member, answer=1)
        investigator.member_answered(question=question_2, household_member=household_member, answer=1)
        investigator.member_answered(question=question_3, household_member=household_member, answer=1)
        self.assertEqual(None, household_member.next_question())
        self.assertTrue(household_member.survey_completed())

    def test_should_know_if_survey_is_pending(self):
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        condition.groups.add(member_group)
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                  location=kampala,
                                                  backend=backend)

        household = Household.objects.create(investigator=investigator, uid=0)

        household_member = HouseholdMember.objects.create(surname="Member",
                                                               date_of_birth=date(1980, 2, 2), male=False, household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch.open_for_location(investigator.location)
        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group, batch=batch)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group, batch=batch)

        self.assertTrue(household_member.pending_surveys())
        investigator.member_answered(question_1,household_member,answer=1)
        self.assertTrue(household_member.pending_surveys())
        investigator.member_answered(question_2,household_member,answer=1)
        self.assertTrue(household_member.survey_completed())
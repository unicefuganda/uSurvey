from datetime import date
from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import HouseholdMemberGroup, Question, GroupCondition, Investigator, Backend, Household, HouseholdMember


class HouseholdMemberGroupTest(TestCase):

    def test_fields(self):
        group = HouseholdMemberGroup()
        fields = [str(item.attname) for item in group._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'order']:
            self.assertIn(field, fields)

    def test_store(self):
        hmg = HouseholdMemberGroup.objects.create(name="5 to 6 years")
        self.failUnless(hmg.id)
        self.failUnless(hmg.created)
        self.failUnless(hmg.modified)
        self.assertEquals("5 to 6 years", hmg.name)
        self.assertEquals(0, hmg.order)

    def test_knows_all_the_questions_associated(self):
        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        another_member_group = HouseholdMemberGroup.objects.create(name="7 to 10 years", order=1)

        question_1 = Question.objects.create(identifier = "identifier1",
                                             text = "Question 1", answer_type = 'number',
                                             order = 1, subquestion = False, group = member_group)
        question_2 = Question.objects.create(identifier = "identifier1", text = "Question 2",
                                             answer_type = 'number', order = 2,
                                             subquestion = False, group = member_group)
        question_3 = Question.objects.create(identifier = "identifier1", text = "Question 3",
                                             answer_type = 'number', order = 1,
                                             subquestion = False, group = another_member_group)
        expected_member_questions = [question_1, question_2]
        unexpected_member_questions = [question_3]

        all_questions_for_group = member_group.all_questions()

        self.assertEqual(len(all_questions_for_group), 2)
        [self.assertIn(question, all_questions_for_group) for question in expected_member_questions]
        [self.assertNotIn(question, all_questions_for_group) for question in unexpected_member_questions]

    def test_knows_member_belongs_to_group_from_a_selected_household_member(self):
        age_value = 6
        age_attribute_type = "age"
        gender_attribute_type = "male"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(name='member1', date_of_birth=(date(2013, 8, 30)),
                                                               male=True,
                                                               household=household)


        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value, condition='LESS_THAN')
        age_condition.groups.add(member_group)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True, condition='EQUALS')
        gender_condition.groups.add(member_group)

        self.assertTrue(member_group.belongs_to_group(household_member))

    def test_knows_all_conditions_belonging_to_group(self):
        age_value = 6
        age_attribute_type = "age"
        gender_attribute_type = "male"

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value, condition='LESS_THAN')
        age_condition.groups.add(member_group)

        another_age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value, condition='LESS_THAN')

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True, condition='EQUALS')
        gender_condition.groups.add(member_group)

        member_group_conditions = member_group.get_all_conditions()
        expected_member_conditions = [age_condition, gender_condition]

        self.assertEqual(2, len(member_group_conditions))
        [self.assertIn(condition, member_group_conditions) for condition in expected_member_conditions]
        self.assertNotIn(another_age_condition, member_group_conditions)

    def test_knows_member_does_not_belong_to_group_from_a_selected_household_member(self):
        age_value = 6
        age_attribute_type = "Age"
        gender_attribute_type = "Male"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(name='member1', date_of_birth=(date(2000, 8, 30)),
                                                               male=False,
                                                               household=household)


        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value, condition='LESS_THAN')
        age_condition.groups.add(member_group)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True, condition='EQUALS')
        gender_condition.groups.add(member_group)

        self.assertFalse(member_group.belongs_to_group(household_member))

    def test_knows_member_belongs_to_one_group_but_not_another_from_a_selected_household_member(self):
        age_value = 6
        age_attribute_type = "Age"
        gender_attribute_type = "Male"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(name='member1', date_of_birth=(date(2013, 8, 30)),
                                                               male=False,
                                                               household=household)


        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value, condition='LESS_THAN')
        age_condition.groups.add(member_group)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True, condition='EQUALS')
        gender_condition.groups.add(member_group)

        self.assertTrue(member_group.has_condition(household_member, age_condition))
        self.assertFalse(member_group.has_condition(household_member, gender_condition))

    def test_knows_member_belongs_to_gender_group_for_a_selected_household_member(self):
        gender_attribute_type = "Male"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(name='member1', date_of_birth=(date(2013, 8, 30)),
                                                               male=True,
                                                               household=household)


        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True, condition='EQUALS')
        gender_condition.groups.add(member_group)

        self.assertTrue(member_group.has_condition(household_member, gender_condition))

    def test_knows_member_belongs_to_age_group_for_a_selected_household_member(self):
        age_value = 6
        age_attribute_type = "Age"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(name='member1', date_of_birth=(date(2013, 8, 30)),
                                                               male=False,
                                                               household=household)


        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value, condition='LESS_THAN')
        age_condition.groups.add(member_group)

        self.assertTrue(member_group.has_condition(household_member, age_condition))
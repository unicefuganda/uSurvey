from datetime import date
from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Batch
from survey.models.question import Question
from survey.models.investigator import Investigator
from survey.models.backend import Backend
from survey.models.households import Household, HouseholdMember, HouseholdHead
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition


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

    def test_no_last_answered_question_returns_false_for_all_questions_answered(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        batch = Batch.objects.create(name="BATCH A", order=1)
        batch.open_for_location(investigator.location)
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2008, 8, 30)),
                                                          male=False,
                                                          household=household)

        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        self.assertTrue(member_group.all_questions_answered(household_member))

    def test_knows_all_the_questions_associated(self):
        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        another_member_group = HouseholdMemberGroup.objects.create(name="7 to 10 years", order=1)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group)
        question_3 = Question.objects.create(identifier="identifier1", text="Question 3",
                                             answer_type='number', order=1,
                                             subquestion=False, group=another_member_group)
        expected_member_questions = [question_1, question_2]
        unexpected_member_questions = [question_3]

        all_questions_for_group = member_group.all_questions()

        self.assertEqual(len(all_questions_for_group), 2)
        [self.assertIn(question, all_questions_for_group) for question in expected_member_questions]
        [self.assertNotIn(question, all_questions_for_group) for question in unexpected_member_questions]
        self.assertEqual(2, member_group.maximum_question_order())
        self.assertEqual(1, another_member_group.maximum_question_order())

    def test_knows_how_to_get_group_first_question(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        batch = Batch.objects.create(name="BATCH A", order=1)
        batch.open_for_location(investigator.location)
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2008, 8, 30)),
                                                          male=False,
                                                          household=household)

        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        another_member_group = HouseholdMemberGroup.objects.create(name="7 to 8 years", order=1)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group, batch=batch)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group, batch=batch)

        question_3 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=1,
                                             subquestion=False, group=another_member_group, batch=batch)

        self.assertEqual(question_1, member_group.first_question(household_member))
        self.assertNotEqual(question_2, member_group.first_question(household_member))
        self.assertEqual(question_3, another_member_group.first_question(household_member))

    def test_knows_how_to_get_group_last_question(self):
        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        another_member_group = HouseholdMemberGroup.objects.create(name="7 to 8 years", order=1)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group)

        self.assertEqual(question_2, member_group.last_question())
        self.assertNotEqual(question_1, member_group.last_question())

    def test_knows_all_questions_in_group_is_answered(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        less_condition = GroupCondition.objects.create(attribute="age", condition="GREATER_THAN", value=4)
        greater_condition = GroupCondition.objects.create(attribute="age", condition="LESS_THAN", value=6)
        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        less_condition.groups.add(member_group)
        greater_condition.groups.add(member_group)

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

        investigator.member_answered(question=question_1, household_member=household_member, answer=1)
        investigator.member_answered(question=question_2, household_member=household_member, answer=1)
        self.assertTrue(member_group.all_questions_answered(household_member))

    def test_knows_how_to_get_all_unanswered_open_batch_question_for_member(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        less_condition = GroupCondition.objects.create(attribute="age", condition="GREATER_THAN", value=4)
        greater_condition = GroupCondition.objects.create(attribute="age", condition="LESS_THAN", value=6)
        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        less_condition.groups.add(member_group)
        greater_condition.groups.add(member_group)

        batch = Batch.objects.create(name="BATCH A", order=1)
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2008, 8, 30)),
                                                          male=False,
                                                          household=household)
        batch.open_for_location(investigator.location)
        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group, batch=batch)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group, batch=batch)
        self.assertIn(question_1, member_group.all_unanswered_open_batch_questions(household_member))
        self.assertIn(question_2, member_group.all_unanswered_open_batch_questions(household_member))

        investigator.member_answered(question=question_1, household_member=household_member, answer=1)

        self.assertNotIn(question_1, member_group.all_unanswered_open_batch_questions(household_member))
        self.assertIn(question_2, member_group.all_unanswered_open_batch_questions(household_member))

        batch.close_for_location(investigator.location)
        self.assertNotIn(question_1, member_group.all_unanswered_open_batch_questions(household_member))
        self.assertNotIn(question_2, member_group.all_unanswered_open_batch_questions(household_member))

    def test_knows_member_belongs_to_group_from_a_selected_household_member(self):
        age_value = 6
        age_attribute_type = "age"
        gender_attribute_type = "GENDER"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=True,
                                                          household=household)

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                      condition='LESS_THAN')
        age_condition.groups.add(member_group)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True,
                                                         condition='EQUALS')
        gender_condition.groups.add(member_group)

        self.assertTrue(member_group.belongs_to_group(household_member))

    def test_knows_all_conditions_belonging_to_group(self):
        age_value = 6
        age_attribute_type = "age"
        gender_attribute_type = "GENDER"

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                      condition='LESS_THAN')
        age_condition.groups.add(member_group)

        another_age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                              condition='LESS_THAN')

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True,
                                                         condition='EQUALS')
        gender_condition.groups.add(member_group)

        member_group_conditions = member_group.get_all_conditions()
        expected_member_conditions = [age_condition, gender_condition]

        self.assertEqual(2, len(member_group_conditions))
        [self.assertIn(condition, member_group_conditions) for condition in expected_member_conditions]
        self.assertNotIn(another_age_condition, member_group_conditions)

    def test_knows_member_does_not_belong_to_group_from_a_selected_household_member(self):
        age_value = 6
        age_attribute_type = "Age"
        gender_attribute_type = "GENDER"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2000, 8, 30)),
                                                          male=False,
                                                          household=household)

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                      condition='LESS_THAN')
        age_condition.groups.add(member_group)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True,
                                                         condition='EQUALS')
        gender_condition.groups.add(member_group)

        self.assertFalse(member_group.belongs_to_group(household_member))

    def test_knows_member_belongs_to_one_group_but_not_another_from_a_selected_household_member(self):
        age_value = 6
        age_attribute_type = "Age"
        gender_attribute_type = "GENDER"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=False,
                                                          household=household)

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                      condition='LESS_THAN')
        age_condition.groups.add(member_group)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True,
                                                         condition='EQUALS')
        gender_condition.groups.add(member_group)

        self.assertTrue(member_group.has_condition(household_member, age_condition))
        self.assertFalse(member_group.has_condition(household_member, gender_condition))

    def test_knows_member_does_not_belong_to_general_group(self):
        age_value = 6
        age_attribute_type = "Age"
        gender_attribute_type = "GENDER"
        general_attribute_type = "Head"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=False,
                                                          household=household)

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        general_group = HouseholdMemberGroup.objects.create(name="General", order=1)
        head_condition = GroupCondition.objects.create(attribute=general_attribute_type, value=True,
                                                       condition='EQUALS')
        head_condition.groups.add(general_group)

        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                      condition='LESS_THAN')
        age_condition.groups.add(member_group)
        self.assertFalse(general_group.has_condition(household_member, head_condition))

    def test_knows_head_belongs_to_general_group(self):
        age_value = 6
        age_attribute_type = "Age"
        gender_attribute_type = "GENDER"
        general_attribute_type = "Head"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdHead.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=False,
                                                          household=household)

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        general_group = HouseholdMemberGroup.objects.create(name="General", order=1)
        head_condition = GroupCondition.objects.create(attribute=general_attribute_type, value=True,
                                                       condition='EQUALS')
        head_condition.groups.add(general_group)

        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                      condition='LESS_THAN')
        age_condition.groups.add(member_group)
        self.assertTrue(general_group.has_condition(household_member, head_condition))


    def test_knows_member_belongs_to_gender_group_for_a_selected_household_member(self):
        gender_attribute_type = "GENDER"

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=True,
                                                          household=household)

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True,
                                                         condition='EQUALS')
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
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=False,
                                                          household=household)

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                      condition='LESS_THAN')
        age_condition.groups.add(member_group)

        self.assertTrue(member_group.has_condition(household_member, age_condition))

    def test_last_question_returns_none_if_there_is_no_questions_in_group(self):
        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)

        self.assertIsNone(member_group.last_question())

    def test_knows_all_group_questions_in_an_open_batches_has_been_answered(self):
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
        batch_2 = Batch.objects.create(name="BATCH A", order=1)

        batch.open_for_location(investigator.location)
        batch_2.open_for_location(investigator.location)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group, batch=batch)

        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group, batch=batch_2)

        self.assertEqual(2, len(member_group.all_unanswered_open_batch_questions(household_member)))

        batch_2.close_for_location(investigator.location)
        self.assertEqual(1, len(member_group.all_unanswered_open_batch_questions(household_member)))

        investigator.member_answered(question_1, household_member, answer=1)
        self.assertEqual(0, len(member_group.all_unanswered_open_batch_questions(household_member)))

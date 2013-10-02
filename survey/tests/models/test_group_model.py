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

    def test_knows_all_conditions_belonging_to_group(self):
        age_value = 6
        age_attribute_type = "age"
        gender_attribute_type = "GENDER"

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                      condition='LESS_THAN')
        age_condition.groups.add(member_group)

        another_age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=15,
                                                              condition='LESS_THAN')

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True,
                                                         condition='EQUALS')
        gender_condition.groups.add(member_group)

        member_group_conditions = member_group.get_all_conditions()
        expected_member_conditions = [age_condition, gender_condition]

        self.assertEqual(2, len(member_group_conditions))
        [self.assertIn(condition, member_group_conditions) for condition in expected_member_conditions]
        self.assertNotIn(another_age_condition, member_group_conditions)

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

        batch.open_for_location(investigator.location)
        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group)

        question_1.batches.add(batch)

        self.assertEqual(question_1, household_member.next_unanswered_question_in(member_group, batch, 0))

        investigator.member_answered(question_1, household_member, answer=1, batch=batch)

        self.assertEqual(None, household_member.next_unanswered_question_in(member_group, batch, 0))

    def test_should_return_zero_if_no_group_created_yet(self):
        HouseholdMemberGroup.objects.all().delete()

        self.assertEqual(0, HouseholdMemberGroup.max_order())

    def test_should_return_max_order_of_all_groups(self):
        HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=7)
        HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=3)

        self.assertEqual(7, HouseholdMemberGroup.max_order())

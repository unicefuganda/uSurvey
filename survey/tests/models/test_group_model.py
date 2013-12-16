from datetime import date
from random import randint
from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Batch, BatchQuestionOrder, Survey, EnumerationArea
from survey.models.question import Question
from survey.models.investigator import Investigator
from survey.models.backend import Backend
from survey.models.households import Household, HouseholdMember, HouseholdHead
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition
from survey.tests.base_test import BaseTest


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
        batch = Batch.objects.create(name='Batch A', order=1)
        question_1.batches.add(batch)
        question_2.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=2)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=1)

        self.assertEqual(question_1, member_group.last_question(batch))
        self.assertNotEqual(question_2, member_group.last_question(batch))

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

        self.assertIsNone(member_group.last_question(None))

    def test_knows_all_group_questions_in_an_open_batches_has_been_answered(self):
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        condition.groups.add(member_group)
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        survey = Survey.objects.create(name="huhu")
        ea = EnumerationArea.objects.create(name="EA2", survey=survey)
        ea.locations.add(kampala)

        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                   ea=ea,
                                                   backend=backend)

        household = Household.objects.create(investigator=investigator, uid=0)

        household_member = HouseholdMember.objects.create(surname="Member",
                                                          date_of_birth=date(1980, 2, 2), male=False,
                                                          household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)

        batch.open_for_location(investigator.location)
        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group)

        question_1.batches.add(batch)

        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)

        self.assertEqual(question_1, household_member.next_unanswered_question_in(member_group, batch, 0))

        investigator.member_answered(question_1, household_member, answer=1, batch=batch)

        self.assertEqual(None, household_member.next_unanswered_question_in(member_group, batch, 0))

    def test_should_return_zero_if_no_group_created_yet(self):
        HouseholdMemberGroup.objects.all().delete()

        self.assertEqual(0, HouseholdMemberGroup.max_order())

    def test_question_knows_de_associate_self_from_group(self):
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        condition.groups.add(member_group)

        Question.objects.create(text="This is a test question", answer_type="multichoice",
                                group=member_group)
        Question.objects.create(text="Another test question", answer_type="multichoice",
                                group=member_group)

        self.failUnless(member_group.question_group.all())
        member_group.remove_related_questions()

        self.failIf(member_group.question_group.all())
        all_questions = Question.objects.filter()

        [self.assertIsNone(question.group) for question in all_questions]

    def test_should_return_max_order_of_all_groups(self):
        HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=7)
        HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=3)

        self.assertEqual(7, HouseholdMemberGroup.max_order())


class SimpleIndicatorGroupCount(BaseTest):
    def create_household_head(self, uid, investigator):
        self.household = Household.objects.create(investigator=investigator, location=investigator.location,
                                                  uid=uid, survey=self.survey)
        return HouseholdHead.objects.create(household=self.household, surname="Name " + str(randint(1, 9999)),
                                            date_of_birth="1990-02-09")

    def setUp(self):
        self.survey = Survey.objects.create(name="haha")
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.region = LocationType.objects.create(name="Region", slug="region")
        self.district = LocationType.objects.create(name="District", slug='district')

        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.west = Location.objects.create(name="WEST", type=self.region, tree_parent=self.uganda)
        self.central = Location.objects.create(name="CENTRAL", type=self.region, tree_parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", tree_parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", tree_parent=self.west, type=self.district)
        ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
        ea.locations.add(self.kampala)

        mbarara_ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
        mbarara_ea.locations.add(self.mbarara)

        backend = Backend.objects.create(name='something')

        self.investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", ea=ea,
                                                        backend=backend)
        self.investigator_2 = Investigator.objects.create(name="Investigator 1", mobile_number="33331",
                                                          ea=mbarara_ea,
                                                          backend=backend)

        self.general_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=2)

        general_condition = GroupCondition.objects.create(attribute="GENERAL", value="HEAD", condition='EQUALS')
        self.general_group.conditions.add(general_condition)

        self.household_head_1 = self.create_household_head(0, self.investigator)
        self.household_head_2 = self.create_household_head(1, self.investigator)
        self.household_head_3 = self.create_household_head(2, self.investigator)
        self.household_head_4 = self.create_household_head(3, self.investigator)
        self.household_head_5 = self.create_household_head(4, self.investigator)

        self.household_head_6 = self.create_household_head(5, self.investigator_2)
        self.household_head_7 = self.create_household_head(6, self.investigator_2)
        self.household_head_8 = self.create_household_head(7, self.investigator_2)
        self.household_head_9 = self.create_household_head(8, self.investigator_2)

    def test_returns_options_counts_given_list_of_locations(self):

        region_group_count = {self.central: {self.general_group.name: 5},
                              self.west: {self.general_group.name: 4}}

        self.assertEquals(self.general_group.hierarchical_result_for(self.uganda, self.survey), region_group_count)

        central_region_general_count = {self.kampala: {self.general_group.name: 5}}
        self.assertEquals(self.general_group.hierarchical_result_for(self.central, self.survey), central_region_general_count)

        west_region_general_count = {self.mbarara: {self.general_group.name: 4}}
        self.assertEquals(self.general_group.hierarchical_result_for(self.west, self.survey), west_region_general_count)
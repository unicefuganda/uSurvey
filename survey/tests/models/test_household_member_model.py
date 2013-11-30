from datetime import date, datetime, timedelta
from django.template.defaultfilters import slugify
from django.test import TestCase
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import Batch, Question, HouseholdMemberBatchCompletion, NumericalAnswer, AnswerRule, BatchQuestionOrder, UnknownDOBAttribute, MultiChoiceAnswer, QuestionOption
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition
from survey.models.households import HouseholdMember, Household, HouseholdHead
from survey.models.backend import Backend
from survey.models.investigator import Investigator
from django.utils.timezone import utc
from mock import patch


class HouseholdMemberTest(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(name="BATCH 1", order=1)

    def test_should_have_fields_required(self):
        household_member = HouseholdMember()
        fields = [str(item.attname) for item in household_member._meta.fields]

        field_list_expected = ['surname', 'first_name', 'male', 'date_of_birth', 'household_id']

        [self.assertIn(field_expected, fields) for field_expected in field_list_expected]

    def test_should_validate_household_member_belongs_to_household(self):
        village = LocationType.objects.create(name="Village", slug=slugify("village"))
        some_village = Location.objects.create(name="Some village", type=village)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321",
                                                   location=some_village,
                                                   backend=Backend.objects.create(name='something1'))
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
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321",
                                                   location=some_village,
                                                   backend=Backend.objects.create(name='something1'))
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
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321",
                                                   location=some_village,
                                                   backend=Backend.objects.create(name='something1'))
        household = Household.objects.create(investigator=investigator, uid=0)
        fields_data = dict(surname='xyz', male=True, date_of_birth=date(2013, 05, 01), household=household)
        household_member = HouseholdMember.objects.create(**fields_data)

        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        another_member_group = HouseholdMemberGroup.objects.create(name="7 to 10 years", order=1)
        member_group_order_2 = HouseholdMemberGroup.objects.create(name="order 2 group", order=2)
        age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=age_value,
                                                      condition='LESS_THAN')
        age_condition.groups.add(member_group)
        age_condition.groups.add(member_group_order_2)

        another_age_condition = GroupCondition.objects.create(attribute=age_attribute_type, value=7,
                                                              condition='GREATER_THAN')
        another_age_condition.groups.add(another_member_group)

        gender_condition = GroupCondition.objects.create(attribute=gender_attribute_type, value=True,
                                                         condition='EQUALS')
        gender_condition.groups.add(member_group)

        member_groups = household_member.get_member_groups()
        self.assertEqual(len(member_groups), 2)
        self.assertIn(member_group, member_groups)
        self.assertIn(member_group_order_2, member_groups)
        self.assertNotIn(another_member_group, member_groups)

        member_groups = household_member.get_member_groups(order_above=1)
        self.assertEqual(len(member_groups), 1)
        self.assertIn(member_group_order_2, member_groups)

    def test_household_member_is_head(self):
        hhold = Household.objects.create(investigator=Investigator(), uid=0)
        household_head = HouseholdHead.objects.create(household=hhold, surname="Name", date_of_birth='1989-02-02')
        household_member = HouseholdMember.objects.create(household=hhold, surname="name", male=False,
                                                          date_of_birth='1989-02-02')

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

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321",
                                                    location=some_village,
                                                    backend=Backend.objects.create(name='something1'))
        hhold = Household.objects.create(investigator=investigator1, location=investigator1.location, uid=0)
        household_member = HouseholdMember.objects.create(household=hhold, surname="name", male=True,
                                                          date_of_birth=date(1998, 2, 2))

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

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321",
                                                    location=some_village,
                                                    backend=Backend.objects.create(name='something1'))

        self.batch = Batch.objects.create(name="Batch 1", order=1)
        group = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
        group_condition = GroupCondition.objects.create(attribute="GENDER", condition="EQUALS", value=True)
        group_condition.groups.add(group)

        question_1 = Question.objects.create(group=group, text="This is another question", answer_type="number",
                                             order=1)
        question_2 = Question.objects.create(group=group, text="This is a question", answer_type="number", order=2)
        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=self.batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=self.batch, order=2)

        self.batch.open_for_location(uganda)

        hhold = Household.objects.create(investigator=investigator1, uid=0)
        household_member = HouseholdMember.objects.create(household=hhold, surname="name", male=True,
                                                          date_of_birth=date(1998, 2, 2))

        self.assertEqual(question_1, household_member.next_question_in_order(self.batch))

    def test_knows_group_and_question_order_of_next_question_given_current_question(self):
        group = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
        question = Question.objects.create(group=group, text="some question", answer_type="number", order=1)
        question_2 = Question.objects.create(group=group, text="last question", answer_type="number", order=2)

        hhold = Household.objects.create(uid=0)
        household_member = HouseholdMember.objects.create(household=hhold, surname="name", male=True,
                                                          date_of_birth=date(1998, 2, 2))

        question.batches.add(self.batch)
        question_2.batches.add(self.batch)
        BatchQuestionOrder.objects.create(question=question, batch=self.batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=self.batch, order=2)

        group_order, question_order = household_member.get_next_question_orders(None)
        self.assertEqual(0, group_order)
        self.assertEqual(0, question_order)

        group_order, question_order = household_member.get_next_question_orders(question, self.batch)
        self.assertEqual(1, group_order)
        self.assertEqual(1, question_order)

        group_order, question_order = household_member.get_next_question_orders(question_2, self.batch)
        self.assertEqual(2, group_order)
        self.assertEqual(0, question_order)

        subquestion = Question.objects.create(group=group, text="subquestion", answer_type="number", parent=question_2,
                                              subquestion=True)

        group_order, question_order = household_member.get_next_question_orders(subquestion, self.batch)
        self.assertEqual(2, group_order)
        self.assertEqual(0, question_order)

    @patch('survey.models.households.HouseholdMember.get_member_groups')
    def test_knows_next_question_in_order_one_group_after_the_other(self, mock_groups):
        investigator = Investigator.objects.create(name="inv1")

        member_group = HouseholdMemberGroup.objects.create(name="group1", order=0)
        member_group_2 = HouseholdMemberGroup.objects.create(name="group2", order=1)

        batch = Batch.objects.create(name="BATCH A", order=1)

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', household=household,
                                                          date_of_birth=(date(2008, 8, 30)), male=False)

        question_1 = Question.objects.create(identifier="identifier1", text="Question 1",
                                             answer_type='number', order=1, subquestion=False, group=member_group)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2, subquestion=False, group=member_group)

        question_3 = Question.objects.create(identifier="identifier1", text="Question 3",
                                             answer_type='number', order=0, subquestion=False, group=member_group_2)
        question_4 = Question.objects.create(identifier="identifier1", text="Question 4",
                                             answer_type='number', order=1, subquestion=False, group=member_group_2)

        question_1.batches.add(batch)
        question_2.batches.add(batch)
        question_3.batches.add(batch)
        question_4.batches.add(batch)

        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
        BatchQuestionOrder.objects.create(question=question_3, batch=batch, order=3)
        BatchQuestionOrder.objects.create(question=question_4, batch=batch, order=4)

        mock_groups.return_value = [member_group, member_group_2]

        self.assertEqual(question_1, household_member.next_question_in_order(batch))

        investigator.member_answered(question=question_1, household_member=household_member, answer=1, batch=batch)
        self.assertEqual(question_2, household_member.next_question_in_order(batch))

        investigator.member_answered(question=question_2, household_member=household_member, answer=1, batch=batch)
        self.assertEqual(question_3, household_member.next_question_in_order(batch))

        investigator.member_answered(question=question_3, household_member=household_member, answer=1, batch=batch)
        self.assertEqual(question_4, household_member.next_question_in_order(batch))

        investigator.member_answered(question=question_4, household_member=household_member, answer=1, batch=batch)
        self.assertEqual(None, household_member.next_question_in_order(batch))

    @patch('survey.models.households.HouseholdMember.belongs_to')
    def test_knows_next_question_in_order_jumping_groups(self, mock_belongs_to):
        investigator = Investigator.objects.create(name="inv1")

        member_group = HouseholdMemberGroup.objects.create(name="group1", order=0)
        member_group_2 = HouseholdMemberGroup.objects.create(name="group2", order=1)

        batch = Batch.objects.create(name="BATCH A", order=1)

        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', household=household,
                                                          date_of_birth=(date(2008, 8, 30)), male=False)

        question_1 = Question.objects.create(identifier="identifier1", text="Question 1",
                                             answer_type='number', order=1, subquestion=False, group=member_group)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2, subquestion=False, group=member_group)

        question_3 = Question.objects.create(identifier="identifier1", text="Question 3",
                                             answer_type='number', order=0, subquestion=False, group=member_group_2)
        question_4 = Question.objects.create(identifier="identifier1", text="Question 4",
                                             answer_type='number', order=1, subquestion=False, group=member_group_2)

        question_1.batches.add(batch)
        question_2.batches.add(batch)
        question_3.batches.add(batch)
        question_4.batches.add(batch)

        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
        BatchQuestionOrder.objects.create(question=question_3, batch=batch, order=3)
        BatchQuestionOrder.objects.create(question=question_4, batch=batch, order=4)

        mock_belongs_to.return_value = True

        self.assertEqual(question_1, household_member.next_question_in_order(batch))

        next_question = investigator.member_answered(question=question_3, household_member=household_member, answer=1,
                                                     batch=batch)
        self.assertEqual(question_4, next_question)

    def test_should_know_if_survey_is_pending(self):
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        condition.groups.add(member_group)
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                   location=kampala,
                                                   backend=backend)

        household = Household.objects.create(investigator=investigator, location=investigator.location, uid=0)

        household_member = HouseholdMember.objects.create(surname="Member",
                                                          date_of_birth=date(1980, 2, 2), male=False,
                                                          household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch.open_for_location(investigator.location)
        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group)

        question_1.batches.add(batch)
        question_2.batches.add(batch)

        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)

        self.assertTrue(household_member.pending_surveys())
        investigator.member_answered(question_1, household_member, answer=1, batch=batch)
        self.assertTrue(household_member.pending_surveys())
        investigator.member_answered(question_2, household_member, answer=1, batch=batch)
        self.assertTrue(household_member.survey_completed())

    def test_knows_all_open_batches_are_completed_for_multiple_questions(self):
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
                                                          date_of_birth=date(1980, 2, 2), male=False,
                                                          household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch_2 = Batch.objects.create(name="BATCH A", order=1)
        batch.open_for_location(investigator.location)
        batch_2.open_for_location(investigator.location)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group)
        question_1.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)

        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group)
        question_2.batches.add(batch_2)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch_2, order=1)

        investigator.member_answered(question_1, household_member, answer=1, batch=batch)
        investigator.member_answered(question_2, household_member, answer=1, batch=batch_2)

        self.assertFalse(household_member.has_open_batches())

    def test_knows_all_open_batches_are_completed(self):
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
                                                          date_of_birth=date(1980, 2, 2), male=False,
                                                          household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch_2 = Batch.objects.create(name="BATCH A", order=1)

        batch.open_for_location(investigator.location)
        batch_2.open_for_location(investigator.location)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group)
        question_1.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)

        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group)
        question_2.batches.add(batch_2)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch_2, order=1)

        investigator.member_answered(question_1, household_member, answer=1, batch=batch)

        self.assertTrue(household_member.has_open_batches())

    def test_knows_the_next_open_batch(self):
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        condition.groups.add(member_group)
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                   location=kampala,
                                                   backend=backend)

        household = Household.objects.create(investigator=investigator, location=investigator.location, uid=0)

        household_member = HouseholdMember.objects.create(surname="Member",
                                                          date_of_birth=date(1980, 2, 2), male=False,
                                                          household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch_2 = Batch.objects.create(name="BATCH A", order=1)

        batch.open_for_location(investigator.location)
        batch_2.open_for_location(investigator.location)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group)

        question_2 = Question.objects.create(identifier="identifier2",
                                             text="Question 2", answer_type='number',
                                             order=2, subquestion=False, group=member_group)

        question_1.batches.add(batch)
        question_2.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)

        q = Question.objects.create(identifier="identifier3", text="Question 3",
                                    answer_type='number', order=3,
                                    subquestion=False, group=member_group)
        q.batches.add(batch_2)
        BatchQuestionOrder.objects.create(question=q, batch=batch_2, order=1)

        self.assertEqual(household_member.get_next_batch(), batch)
        investigator.member_answered(question_1, household_member, answer=2, batch=batch)
        self.assertEqual(household_member.get_next_batch(), batch)
        investigator.member_answered(question_2, household_member, answer=4, batch=batch)
        self.assertEqual(household_member.get_next_batch(), batch_2)

    def test_household_knows_survey_can_be_retaken(self):
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                   location=kampala,
                                                   backend=backend)

        household = Household.objects.create(investigator=investigator, uid=0)

        household_member = HouseholdMember.objects.create(surname="Member",
                                                          date_of_birth=date(1980, 2, 2), male=False,
                                                          household=household)
        household_member_2 = HouseholdMember.objects.create(surname="Member 2",
                                                            date_of_birth=date(1980, 2, 2), male=False,
                                                            household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch_2 = Batch.objects.create(name="BATCH A", order=1)

        self.assertTrue(household_member.can_retake_survey(batch, 5))
        self.assertTrue(household_member.can_retake_survey(batch_2, 5))
        self.assertTrue(household_member_2.can_retake_survey(batch, 5))
        self.assertTrue(household_member_2.can_retake_survey(batch_2, 5))

        batch.open_for_location(investigator.location)
        batch_2.open_for_location(investigator.location)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member,
                                                      investigator=investigator, household=household_member.household)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member_2,
                                                      investigator=investigator, household=household_member.household)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member,
                                                      investigator=investigator, household=household_member.household)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member_2,
                                                      investigator=investigator, household=household_member.household)

        self.assertTrue(household_member.can_retake_survey(batch, 5))
        self.assertTrue(household_member.can_retake_survey(batch_2, 5))
        self.assertTrue(household_member_2.can_retake_survey(batch, 5))
        self.assertTrue(household_member_2.can_retake_survey(batch_2, 5))

        HouseholdMemberBatchCompletion.objects.all().delete()

        ten_minutes_ago = datetime.utcnow().replace(tzinfo=utc) - timedelta(minutes=20)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member,
                                                      investigator=investigator, household=household_member.household,
                                                      created=ten_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member_2,
                                                      investigator=investigator, household=household_member.household,
                                                      created=ten_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member,
                                                      investigator=investigator, household=household_member.household)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member_2,
                                                      investigator=investigator, household=household_member.household)
        self.assertFalse(household_member.can_retake_survey(batch, 5))
        self.assertFalse(household_member_2.can_retake_survey(batch, 5))
        self.assertTrue(household_member.can_retake_survey(batch_2, 5))
        self.assertTrue(household_member_2.can_retake_survey(batch_2, 5))

        HouseholdMemberBatchCompletion.objects.all().delete()

        three_minutes_ago = datetime.utcnow().replace(tzinfo=utc) - timedelta(minutes=3)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member,
                                                      investigator=investigator, household=household_member.household,
                                                      created=ten_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member_2,
                                                      investigator=investigator, household=household_member.household,
                                                      created=three_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member,
                                                      investigator=investigator, household=household_member.household,
                                                      created=three_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member_2,
                                                      investigator=investigator, household=household_member.household,
                                                      created=ten_minutes_ago)

        self.assertFalse(household_member.can_retake_survey(batch, 5))
        self.assertTrue(household_member_2.can_retake_survey(batch, 5))
        self.assertTrue(household_member.can_retake_survey(batch_2, 5))
        self.assertFalse(household_member_2.can_retake_survey(batch_2, 5))

    def test_should_know_householdmember_has_completed_batch(self):
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                   location=kampala,
                                                   backend=backend)
        self.batch = Batch.objects.create(name="Batch 1", order=1)
        group = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
        group_condition = GroupCondition.objects.create(attribute="GENDER", condition="EQUALS", value=True)
        group_condition.groups.add(group)

        question_1 = Question.objects.create(group=group, text="This is another question", answer_type="number",
                                             order=1)
        question_2 = Question.objects.create(group=group, text="This is a question", answer_type="number", order=2)

        self.batch.questions.add(question_1)
        self.batch.questions.add(question_2)
        BatchQuestionOrder.objects.create(question=question_1, batch=self.batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=self.batch, order=2)

        self.batch.open_for_location(kampala)

        hhold = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(household=hhold, surname="name", male=True,
                                                          date_of_birth=date(1998, 2, 2))
        NumericalAnswer.objects.create(investigator=investigator, question=question_1, householdmember=household_member,
                                       answer=1, household=household_member.household, batch=self.batch)
        self.assertFalse(household_member.has_completed(self.batch))
        NumericalAnswer.objects.create(investigator=investigator, question=question_2, householdmember=household_member,
                                       answer=1, household=household_member.household, batch=self.batch)
        self.assertTrue(household_member.has_completed(self.batch))
        household_member.batch_completed(self.batch)
        self.assertEqual(1, len(household_member.completed_member_batches.all()))

        household_member.mark_past_answers_as_old()
        self.assertFalse(household_member.has_completed(self.batch))
        self.assertEqual(0, len(household_member.completed_member_batches.all()))

    def test_knows_how_to_get_next_unanswered_question(self):
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
                                             order=0, subquestion=False, group=member_group)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=1,
                                             subquestion=False, group=member_group)
        question_1.batches.add(batch)
        question_2.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)

        self.assertEqual(question_1, household_member.next_unanswered_question_in(member_group, batch, 0))
        self.assertEqual(question_2, household_member.next_unanswered_question_in(member_group, batch, 1))
        investigator.member_answered(question=question_1, household_member=household_member, answer=1, batch=batch)

        self.assertNotEqual(question_1, household_member.next_unanswered_question_in(member_group, batch, 0))
        self.assertEqual(question_2, household_member.next_unanswered_question_in(member_group, batch, 1))
        investigator.member_answered(question=question_2, household_member=household_member, answer=1, batch=batch)
        self.assertEqual(None, household_member.next_unanswered_question_in(member_group, batch, 1))

    def test_knows_how_to_get_next_unanswered_question_for_member_given_order(self):
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
                                             order=0, subquestion=False, group=member_group)
        question_2 = Question.objects.create(identifier="identifier1", text="Question 2",
                                             answer_type='number', order=1,
                                             subquestion=False, group=member_group)
        question_3 = Question.objects.create(identifier="identifier1", text="Question 3",
                                             answer_type='number', order=2,
                                             subquestion=False, group=member_group)
        question_1.batches.add(batch)
        question_2.batches.add(batch)
        question_3.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
        BatchQuestionOrder.objects.create(question=question_3, batch=batch, order=3)

        self.assertEqual(question_1, household_member.next_unanswered_question_in(member_group, batch, 0))
        self.assertEqual(question_2, household_member.next_unanswered_question_in(member_group, batch, 1))
        self.assertEqual(question_3, household_member.next_unanswered_question_in(member_group, batch, 2))

        investigator.member_answered(question=question_1, household_member=household_member, answer=1, batch=batch)
        self.assertEqual(question_2, household_member.next_unanswered_question_in(member_group, batch, 1))
        self.assertNotEqual(question_2, household_member.next_unanswered_question_in(member_group, batch, 2))
        self.assertEqual(question_3, household_member.next_unanswered_question_in(member_group, batch, 2))

        household_member.mark_past_answers_as_old()
        self.assertEqual(question_1, household_member.next_unanswered_question_in(member_group, batch, 0))
        self.assertEqual(question_2, household_member.next_unanswered_question_in(member_group, batch, 1))
        self.assertEqual(question_3, household_member.next_unanswered_question_in(member_group, batch, 2))

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

        self.assertTrue(household_member.belongs_to(member_group))

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

        self.assertFalse(household_member.belongs_to(member_group))

    def test_knows_member_belongs_to_one_group_but_not_another(self):
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

        self.assertTrue(household_member.attribute_matches(age_condition))
        self.assertFalse(household_member.attribute_matches(gender_condition))

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
        self.assertFalse(household_member.attribute_matches(head_condition))

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
        self.assertTrue(household_member.attribute_matches(head_condition))

    def test_knows_member_belongs_to_gender_group(self):
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

        self.assertTrue(household_member.attribute_matches(gender_condition))

    def test_knows_member_belongs_to_age_group(self):
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

        self.assertTrue(household_member.attribute_matches(age_condition))

    def test_member_knows_its_location(self):
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))

        household = Household.objects.create(investigator=investigator, location=investigator.location, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=False,
                                                          household=household)
        self.assertEqual(uganda, household_member.location())

    def test_knows_to_mark_answers_as_old(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=False,
                                                          household=household)

        batch = Batch.objects.create(name="Batch 1", order=1)
        group = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
        group_condition = GroupCondition.objects.create(attribute="GENDER", condition="EQUALS", value=True)
        group_condition.groups.add(group)

        question_1 = Question.objects.create(group=group, text="This is another question", answer_type="number",
                                             order=1)
        question_1.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)

        batch.open_for_location(investigator.location)
        investigator.member_answered(question_1, household_member, 1, batch)

        self.assertFalse(NumericalAnswer.objects.filter(question=question_1)[0].is_old)

        household_member.mark_past_answers_as_old()
        self.assertTrue(NumericalAnswer.objects.filter(question=question_1)[0].is_old)

    def test_can_retake_survey_with_no_batch(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=False,
                                                          household=household)
        batch = Batch.objects.create(name="Batch 1", order=1)
        group = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
        group_condition = GroupCondition.objects.create(attribute="GENDER", condition="EQUALS", value=True)
        group_condition.groups.add(group)

        question_1 = Question.objects.create(group=group, text="This is another question", answer_type="number",
                                             order=1)
        question_1.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)

        self.assertTrue(household_member.can_retake_survey(None, 5))
        self.assertFalse(household_member.has_open_batches())
        self.assertFalse(household_member.has_open_batches())

        batch.open_for_location(investigator.location)
        self.assertFalse(household_member.all_questions_answered([question_1], batch))
        investigator.member_answered(question_1, household_member, 1, batch)

        self.assertTrue(household_member.all_questions_answered([question_1], batch))

    def test_get_age(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2003, 8, 30)),
                                                          male=False,
                                                          household=household)
        self.assertEqual(10, household_member.get_age())

    def test_year_of_birth_when_known(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2003, 8, 30)),
                                                          male=False,
                                                          household=household)
        self.assertEqual(2003, household_member.get_year_of_birth())

    def test_year_of_birth_when_not_known(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2003, 8, 30)),
                                                          male=False,
                                                          household=household)
        UnknownDOBAttribute.objects.create(household_member=household_member, type='YEAR')
        self.assertEqual(99, household_member.get_year_of_birth())

    def test_month_of_birth_when_known(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2003, 8, 30)),
                                                          male=False,
                                                          household=household)
        self.assertEqual(8, household_member.get_month_of_birth())

    def test_month_of_birth_when_not_known(self):
        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2003, 8, 30)),
                                                          male=False,
                                                          household=household)
        UnknownDOBAttribute.objects.create(household_member=household_member, type='MONTH')
        self.assertEqual(99, household_member.get_month_of_birth())

    def test_knows_has_not_answered_non_response_questions(self):
        none_response_group = HouseholdMemberGroup.objects.create(name="NON_RESPONSE", order=0)
        non_response_question = Question.objects.create(text="Why did HH-bob not take the survey",
                                                        answer_type=Question.MULTICHOICE, order=1,
                                                        group=none_response_group)

        QuestionOption.objects.create(question=non_response_question, text="House closed", order=1)
        QuestionOption.objects.create(question=non_response_question, text="Household moved", order=2)
        QuestionOption.objects.create(question=non_response_question, text="Refused to answer", order=3)
        QuestionOption.objects.create(question=non_response_question, text="Died", order=4)

        country = LocationType.objects.create(name="Country", slug="country")
        district = LocationType.objects.create(name="District", slug="district")
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        self.batch.open_for_location(kampala)
        investigator = Investigator.objects.create(name="inv1", location=kampala,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0, location=kampala)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2003, 8, 30)),
                                                          male=False,
                                                          household=household)
        self.assertFalse(household_member.has_answered_non_response())

        MultiChoiceAnswer.objects.create(investigator=investigator, batch=self.batch, question=non_response_question,
                                         householdmember=household_member)
        self.assertTrue(household_member.has_answered_non_response())

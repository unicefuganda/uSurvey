from datetime import date, datetime
from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import HouseholdMemberGroup, GroupCondition, Backend, Investigator, Household, Question, HouseholdMemberBatchCompletion, Batch, QuestionModule, BatchQuestionOrder
from survey.models.batch import Batch, BatchLocationStatus
from survey.models.households import HouseholdMember
from survey.models.surveys import Survey
from django.db import IntegrityError


class BatchTest(TestCase):
    def test_fields(self):
        batch = Batch()
        fields = [str(item.attname) for item in batch._meta.fields]
        self.assertEqual(7, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'description', 'order', 'survey_id']:
            self.assertIn(field, fields)


    def test_store(self):
        batch = Batch.objects.create(order=1, name="Batch name")
        self.failUnless(batch.id)

    def test_should_know_if_batch_is_open(self):
        batch = Batch.objects.create(order=1, name="Batch name")
        self.assertFalse(batch.is_open())
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        batch.open_for_location(kampala)
        self.assertTrue(batch.is_open())

    def test_should_assign_order_as_0_if_it_is_the_only_batch(self):
        batch = Batch.objects.create(name="Batch name", description='description')
        batch = Batch.objects.get(name='Batch name')
        self.assertEqual(batch.order, 1)

    def test_should_assign_max_order_plus_one_if_not_the_only_batch(self):
        batch = Batch.objects.create(name="Batch name", description='description')
        batch_1 = Batch.objects.create(name="Batch name_1", description='description')
        batch_1 = Batch.objects.get(name='Batch name_1')
        self.assertEqual(batch_1.order, 2)

    def test_should_open_batch_for_parent_and_descendant_locations(self):
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        masaka = Location.objects.create(name="masaka", type=district, tree_parent=uganda)

        batch = Batch.objects.create(order=1)

        batch.open_for_location(uganda)
        self.assertTrue(batch.is_open_for(uganda))
        self.assertTrue(batch.is_open_for(kampala))
        self.assertTrue(batch.is_open_for(masaka))

    def test_should_be_unique_together_batch_name_and_survey_id(self):
        survey = Survey.objects.create(name="very fast")
        batch_a = Batch.objects.create(survey=survey, name='Batch A', description='description')
        batch = Batch(survey=survey, name=batch_a.name, description='something else')
        self.assertRaises(IntegrityError, batch.save)

    def test_knows_batch_is_complete_if_completion_object_exists_for_member(self):
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 5 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=5, condition="GREATER_THAN")
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

        another_household_member = HouseholdMember.objects.create(surname="Member",
                                                                  date_of_birth=date(1990, 2, 2), male=False,
                                                                  household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)

        batch.open_for_location(investigator.location)

        question = Question.objects.create(identifier="identifier1",
                                           text="Question 1", answer_type='number',
                                           order=1, subquestion=False, group=member_group)
        question.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question, batch=batch, order=1)


        HouseholdMemberBatchCompletion.objects.create(householdmember=household_member, batch=batch,
                                                household=household_member.household)

        self.assertIsNone(household_member.get_next_batch())
        self.assertEqual(batch, another_household_member.get_next_batch())


    def test_knows_has_unanswered_questions_in_member_group(self):
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 5 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=5, condition="GREATER_THAN")
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

        another_household_member = HouseholdMember.objects.create(surname="Member",
                                                                  date_of_birth=date(2013, 2, 2), male=False,
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

        question_2 = Question.objects.create(identifier="identifier2",
                                             text="Question 2", answer_type='number',
                                             order=2, subquestion=False, group=member_group)
        question_2.batches.add(batch_2)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch_2, order=1)

        self.assertTrue(batch.has_unanswered_question(household_member))
        self.assertTrue(batch_2.has_unanswered_question(household_member))

        investigator.member_answered(question_1, household_member, answer=2, batch=batch)
        self.assertFalse(batch.has_unanswered_question(household_member))
        self.assertTrue(batch_2.has_unanswered_question(household_member))

        investigator.member_answered(question_2, household_member, answer=2, batch=batch_2)
        self.assertFalse(batch.has_unanswered_question(household_member))
        self.assertFalse(batch_2.has_unanswered_question(household_member))

        self.assertFalse(batch.has_unanswered_question(another_household_member))
        self.assertFalse(batch_2.has_unanswered_question(another_household_member))

    def test_batch_knows_all_groups_it_has(self):
        batch = Batch.objects.create(name="Batch name", description='description')
        group_1 = HouseholdMemberGroup.objects.create(name="Group 1", order=0)
        group_2 = HouseholdMemberGroup.objects.create(name="Group 2", order=1)
        group_3 = HouseholdMemberGroup.objects.create(name="Group 3", order=2)

        question_1 = Question.objects.create(group=group_1,
                                             text="Question 1", answer_type=Question.NUMBER,
                                             identifier="identifier", order=1)

        question_2 = Question.objects.create(group=group_2,
                                             text="Question 1", answer_type=Question.NUMBER,
                                             identifier="identifier", order=1)

        question_3 = Question.objects.create(group=group_3,
                                             text="Question 1", answer_type=Question.NUMBER,
                                             identifier="identifier", order=1)

        question_1.batches.add(batch)
        question_2.batches.add(batch)
        question_3.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
        BatchQuestionOrder.objects.create(question=question_3, batch=batch, order=3)


        batch_groups = [group_1, group_2, group_3]
        self.assertEqual(3, len(batch.get_groups()))
        [self.assertIn(batch_group, batch.get_groups()) for batch_group in batch_groups]

    def test_knows_open_batches_from_other_surveys_given_location(self):
        survey = Survey.objects.create(name='survey name', description= 'survey descrpition', type=False, sample_size=10)
        another_survey = Survey.objects.create(name='survey name 2', description= 'survey descrpition 2', type=False, sample_size=10)
        batch = Batch.objects.create(name="Batch name", description='description', survey=survey)
        another_batch = Batch.objects.create(name="Batch name", description='description', survey=another_survey)

        kampala = Location.objects.create(name="Kampala")
        another_batch.open_for_location(kampala)

        self.assertEqual(1, batch.other_surveys_with_open_batches_in(kampala).count())
        self.assertIn(another_survey, batch.other_surveys_with_open_batches_in(kampala))


class BatchLocationStatusTest(TestCase):
    def test_store(self):
        batch_1 = Batch.objects.create(order=1)
        kampala = Location.objects.create(name="Kampala")
        batch_location_status = BatchLocationStatus.objects.create(batch=batch_1, location=kampala)
        self.failUnless(batch_location_status.id)
        self.assertFalse(batch_location_status.non_response)

    def test_open_and_close_for_location(self):
        batch_1 = Batch.objects.create(order=1)
        batch_2 = Batch.objects.create(order=2)
        kampala = Location.objects.create(name="Kampala")
        abim = Location.objects.create(name="Abim")
        investigator_1 = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=kampala,
                                                     backend=Backend.objects.create(name='something'))
        investigator_2 = Investigator.objects.create(name="Investigator 2", mobile_number="2", location=abim,
                                                     backend=Backend.objects.create(name='something1'))

        self.assertEqual(len(investigator_1.get_open_batch()), 0)
        self.assertEqual(len(investigator_2.get_open_batch()), 0)

        batch_1.open_for_location(kampala)
        batch_2.open_for_location(abim)

        self.assertEqual(investigator_1.get_open_batch(), [batch_1])
        self.assertEqual(investigator_2.get_open_batch(), [batch_2])

        batch_1.close_for_location(kampala)
        batch_2.close_for_location(abim)

        self.assertEqual(len(investigator_1.get_open_batch()), 0)
        self.assertEqual(len(investigator_2.get_open_batch()), 0)

    def test_get_next_question_from_batch(self):
        batch = Batch.objects.create(name="Batch 1", order=1)
        batch_2 = Batch.objects.create(name="Batch 2", order=2)
        kampala = Location.objects.create(name="Kampala")
        abim = Location.objects.create(name="Abim")
        group_1 = HouseholdMemberGroup.objects.create(name="Group 1", order=0)

        module = QuestionModule.objects.create(name="Education")

        question_1 = Question.objects.create(module=module, group=group_1,
                                             text="Question 1", answer_type=Question.NUMBER,
                                             identifier="identifier", order=1)

        question_2 = Question.objects.create(module=module, group=group_1,
                                             text="Question 2", answer_type=Question.NUMBER,
                                             identifier="identifier", order=2)

        question_3 = Question.objects.create(module=module, group=group_1,
                                             text="Question 3", answer_type=Question.NUMBER,
                                             identifier="identifier", order=1)

        question_1.batches.add(batch)
        question_2.batches.add(batch)
        question_3.batches.add(batch_2)


        batch.open_for_location(kampala)
        self.assertIsNone(batch.get_next_open_batch(batch.order, kampala))

        batch_2.open_for_location(kampala)
        self.assertEqual(batch_2, batch.get_next_open_batch(batch.order, kampala))

        self.assertEqual(question_1, batch.get_next_question(0, kampala))
        self.assertEqual(question_2, batch.get_next_question(1, kampala))
        self.assertEqual(question_3, batch.get_next_question(2, kampala))

        batch.close_for_location(kampala)
        self.assertEqual(question_3, batch.get_next_question(0, kampala))

        self.assertEqual(batch_2, batch.currently_open_for(kampala))
        self.assertIsNone(batch.currently_open_for(abim))

    def test_knows_whether_can_be_deleted(self):
        district = LocationType.objects.create(name="District", slug='district')
        kampala = Location.objects.create(name="Kampala", type=district)
        survey = Survey.objects.create(name='survey name', description='survey descrpition', type=False,
                                            sample_size=10)
        batch = Batch.objects.create(order=1, name="Batch A", survey=survey)
        investigator = Investigator.objects.create(mobile_number="123456789", name="Rajni", location=kampala)
        household = Household.objects.create(investigator=investigator, location=investigator.location)
        member = HouseholdMember.objects.create(surname="haha", date_of_birth=date(1990, 02, 01), household=household)
        group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        female = GroupCondition.objects.create(attribute="gender", value=True, condition="EQUALS")
        group.conditions.add(female)
        module = QuestionModule.objects.create(name="Education")
        question_1 = Question.objects.create(group=group, text="Haha?", module=module, answer_type=Question.NUMBER,
                                             order=1)
        question_2 = Question.objects.create(group=group, text="Haha?", module=module, answer_type=Question.NUMBER,
                                             order=2)
        question_3 = Question.objects.create(group=group, text="Haha?", module=module, answer_type=Question.NUMBER,
                                             order=3)

        question_1.batches.add(batch)
        question_2.batches.add(batch)
        question_3.batches.add(batch)

        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
        BatchQuestionOrder.objects.create(question=question_3, batch=batch, order=3)


        batch.open_for_location(kampala)
        investigator.member_answered(question_1, member, 1, batch)
        investigator.member_answered(question_2, member, 1, batch)
        investigator.member_answered(question_3, member, 1, batch)
        batch.close_for_location(kampala)
        self.assertFalse(batch.can_be_deleted())


class HouseholdBatchCompletionTest(TestCase):
    def test_store(self):
        batch = Batch.objects.create(order=1)
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=kampala,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)

        batch_completion = HouseholdMemberBatchCompletion.objects.create(household=household, investigator=investigator,
                                                                   batch=batch)
        self.failUnless(batch_completion.id)

    def test_completed(self):
        batch = Batch.objects.create(order=1)
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=kampala,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)
        member = HouseholdMember.objects.create(household=household, date_of_birth=date(2011,1,11))

        self.assertFalse(household.has_completed_batch(batch))

        household.batch_completed(batch)
        member.batch_completed(batch)

        self.assertTrue(household.has_completed_batch(batch))

        household.batch_reopen(batch)

        self.assertFalse(household.has_completed_batch(batch))


class BatchExportReportTest(TestCase):
    def test_knows_headers_for_batch_with_questions(self):
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(name='District', slug='district')
        county = LocationType.objects.create(name='County', slug='county')
        subcounty = LocationType.objects.create(name='Subcounty', slug='subcounty')
        parish = LocationType.objects.create(name='Parish', slug='parish')
        village = LocationType.objects.create(name='Village', slug='village')
        survey = Survey.objects.create(name='survey name', description='survey descrpition', type=False,
                                            sample_size=10)
        kampala = Location.objects.create(name="Kampala", type=district)

        batch = Batch.objects.create(order=1, name="Batch A", survey=survey)
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=kampala,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, location=kampala, survey=survey, uid=0,
                                             household_code='00010001')
        member = HouseholdMember.objects.create(household=household, surname="Member 1", date_of_birth=date(2011, 1, 11))


        group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        module = QuestionModule.objects.create(name="Education")
        question_1 = Question.objects.create(group=group, text="Question 1", module=module, answer_type=Question.NUMBER,
                                             order=1, identifier='Q1')
        question_2 = Question.objects.create(group=group, text="Question 2", module=module, answer_type=Question.MULTICHOICE,
                                             order=2, identifier='Q2')
        question_3 = Question.objects.create(group=group, text="Question 3", module=module, answer_type=Question.NUMBER,
                                             order=3, identifier='Q3')

        question_1.batches.add(batch)
        question_2.batches.add(batch)
        question_3.batches.add(batch)

        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
        BatchQuestionOrder.objects.create(question=question_3, batch=batch, order=3)

        header_structure = [country.name, district.name, county.name, subcounty.name, parish.name, village.name,
                            'Household ID', 'Name', 'Age', 'Month of Birth', 'Year of Birth', 'Gender', question_1.identifier,
                            question_2.identifier, '', question_3.identifier]
        expected_questions = [question_1, question_2, question_3]

        batch_questions, headers = batch.set_report_headers()
        self.assertEqual(header_structure, headers)
        self.assertEqual(expected_questions, batch_questions)

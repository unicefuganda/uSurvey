from datetime import date
from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import HouseholdMemberGroup, GroupCondition, Backend, Investigator, Household, Question
from survey.models.batch import Batch
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

    def test_should_assign_order_as_0_if_it_is_the_only_batch(self):
        batch = Batch.objects.create(name="Batch name",description='description')
        batch = Batch.objects.get(name='Batch name')
        self.assertEqual(batch.order,1)

    def test_should_assign_max_order_plus_one_if_not_the_only_batch(self):
        batch = Batch.objects.create(name="Batch name",description='description')
        batch_1 = Batch.objects.create(name="Batch name_1",description='description')
        batch_1 = Batch.objects.get(name='Batch name_1')
        self.assertEqual(batch_1.order,2)

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
        batch_a = Batch.objects.create(survey=survey, name='Batch A',description='description')
        batch = Batch(survey=survey, name=batch_a.name, description='something else')
        self.assertRaises(IntegrityError, batch.save)

    def test_knows_all_open_batches(self):

        batch = Batch.objects.create(name="Batch name",description='description')
        batch_1 = Batch.objects.create(name="Batch name_1",description='description')

        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        masaka = Location.objects.create(name="masaka", type=district, tree_parent=uganda)

        self.assertEqual([], Batch.open_batches(uganda))

        batch.open_for_location(uganda)

        self.assertIn(batch, Batch.open_batches(uganda))
        self.assertNotIn(batch_1, Batch.open_batches(uganda))

        open_batches = [batch, batch_1]
        batch_1.open_for_location(uganda)
        [self.assertIn(open_batch, Batch.open_batches(uganda)) for open_batch in open_batches]

        batch_1.close_for_location(uganda)
        batch_1.open_for_location(kampala)

        self.assertIn(batch, Batch.open_batches(uganda))
        self.assertNotIn(batch_1, Batch.open_batches(uganda))

    def test_knows_has_unanswered_questions_in_member_group(self):
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 5 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=5, condition="GREATER_THAN")
        condition.groups.add(member_group)
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                   location=kampala,
                                                   backend=backend)

        household = Household.objects.create(investigator=investigator, uid=0)

        household_member = HouseholdMember.objects.create(surname="Member",
                                                          date_of_birth=date(1980, 2, 2), male=False, household=household)

        another_household_member = HouseholdMember.objects.create(surname="Member",
                                                          date_of_birth=date(2013, 2, 2), male=False, household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch_2 = Batch.objects.create(name="BATCH A", order=1)

        batch.open_for_location(investigator.location)
        batch_2.open_for_location(investigator.location)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group, batch=batch)

        question_2 = Question.objects.create(identifier="identifier2",
                                             text="Question 2", answer_type='number',
                                             order=2, subquestion=False, group=member_group, batch=batch_2)

        self.assertTrue(batch.has_unanswered_question(household_member))
        self.assertTrue(batch_2.has_unanswered_question(household_member))

        investigator.member_answered(question_1, household_member, answer=2)
        self.assertFalse(batch.has_unanswered_question(household_member))
        self.assertTrue(batch_2.has_unanswered_question(household_member))

        investigator.member_answered(question_2, household_member, answer=2)
        self.assertFalse(batch.has_unanswered_question(household_member))
        self.assertFalse(batch_2.has_unanswered_question(household_member))

        self.assertFalse(batch.has_unanswered_question(another_household_member))
        self.assertFalse(batch_2.has_unanswered_question(another_household_member))
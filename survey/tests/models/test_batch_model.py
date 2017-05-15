from django.test import TestCase
from survey.models.locations import LocationType, Location
from survey.models import Backend
from survey.models import Batch
from survey.models import EnumerationArea
from survey.models import Interviewer
from survey.models import Question
from survey.models import QuestionModule
# from survey.models.batch_question_order import BatchQuestionOrder
from survey.models.batch import Batch, BatchLocationStatus
from survey.models.surveys import Survey
from django.db import IntegrityError


class BatchTest(TestCase):

    def test_fields(self):
        batch = Batch()
        fields = [str(item.attname) for item in batch._meta.fields]
        self.assertEqual(8, len(fields))
        for field in ['id', 'created', 'modified', 'order', 'name', 'description', 'survey_id', 'start_question_id']:
            self.assertIn(field, fields)

    def test_store(self):
        batch = Batch.objects.create(order=1, name="Batch name")
        self.failUnless(batch.id)

    def test_should_know_if_batch_is_open(self):
        batch = Batch.objects.create(order=1, name="Batch name")
        self.assertFalse(batch.is_open())
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(
            name='District', parent=country, slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, parent=uganda)
        batch.open_for_location(kampala)
        self.assertTrue(batch.is_open())

    def test_should_assign_order_as_0_if_it_is_the_only_batch(self):
        batch = Batch.objects.create(
            name="Batch name", description='description')
        batch = Batch.objects.get(name='Batch name')
        self.assertEqual(batch.order, 1)

    def test_should_assign_max_order_plus_one_if_not_the_only_batch(self):
        batch = Batch.objects.create(
            name="Batch name", description='description')
        batch_1 = Batch.objects.create(
            name="Batch name_1", description='description')
        batch_1 = Batch.objects.get(name='Batch name_1')
        self.assertEqual(batch_1.order, 2)

    def test_should_be_unique_together_batch_name_and_survey_id(self):
        survey = Survey.objects.create(name="very fast")
        batch_a = Batch.objects.create(
            survey=survey, name='Batch A', description='description')
        batch = Batch(survey=survey, name=batch_a.name,
                      description='something else')
        self.assertRaises(IntegrityError, batch.save)

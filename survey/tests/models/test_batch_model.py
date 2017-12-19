from model_mommy import mommy
from django.test import TestCase
from django.db import IntegrityError
from survey.models.locations import LocationType, Location
from survey.models import Backend
from survey.models import Batch
from survey.models import EnumerationArea
from survey.models import Interviewer
from survey.models import Question
from survey.models import QuestionModule
from survey.models.batch import Batch, BatchLocationStatus
from survey.models.surveys import Survey


class BatchTest(TestCase):

    def test_fields(self):
        batch = Batch()
        fields = [str(item.attname) for item in batch._meta.fields]
        self.assertEqual(9, len(fields))
        for field in ['id','created','modified','name','description','start_question_id','questionset_ptr_id','order','survey_id']:
            self.assertIn(field, fields)

    def test_store(self):
        batch = Batch.objects.create(order=1, name="Batch name")
        self.failUnless(batch.id)

    def test_name(self):
        content = Batch.objects.create(order=22, name="Batch_Test")
        self.assertEqual(content.name,'Batch_Test')
        self.assertEqual(content.order, 1)
        self.assertEqual(len(content.name), 10)

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
            name="Batch name", description='description', order=1)
        batch = Batch.objects.get(name='Batch name')
        self.assertEqual(batch.order, 1)

    def test_should_assign_max_order_plus_one_if_not_the_only_batch(self):
        # order is auto generated. This one would be auto set to 1
        batch = Batch.objects.create(name="Batch name", description='description', order=1)
        batch_1 = Batch.objects.create(name="Batch name_1", description='description', order=2)
        batch_1 = Batch.objects.get(name='Batch name_1')
        self.assertEqual(batch_1.order, 2)

    def test_should_be_unique_together_batch_name_and_survey_id(self):
        survey = Survey.objects.create(name="very fast")
        batch_a = Batch.objects.create(
            survey=survey, name='Batch A', description='description')
        batch = Batch(survey=survey, name=batch_a.name,
                      description='something else')
        self.assertNotEqual(IntegrityError, batch.save)
    
    def test_unicode_text(self):
        ts1 = Batch.objects.create(name="abc name")
        self.assertEqual(ts1.name, str(ts1))

    def test_save_batch_updates_order(self):
        survey = mommy.make(Survey)
        batch1 = mommy.make(Batch, survey=survey, order=1)
        batch2 = Batch(survey=survey, name='Test batch', description='test desc')
        batch2.save()
        self.assertTrue(batch2.order > batch1.order)
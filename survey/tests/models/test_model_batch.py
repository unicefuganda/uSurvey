from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Batch

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
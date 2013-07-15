from django.test import TestCase
from django.test.client import Client

from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import *
from survey import investigator_configs
from survey.views.aggregates import *

class AggregatesPageTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_page(self):
        country = LocationType.objects.create(name = 'Country', slug = 'country')
        city = LocationType.objects.create(name = 'City', slug = 'city')

        uganda = Location.objects.create(name='Uganda', type = country)
        abim = Location.objects.create(name='Abim', tree_parent = uganda, type = city)
        kampala = Location.objects.create(name='Kampala', tree_parent = uganda, type = city)
        kampala_city = Location.objects.create(name='Kampala City', tree_parent = kampala, type = city)

        response = self.client.get('/aggregates/status')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/status.html', templates)
        self.assertEquals(len(response.context['batches']), 0)
        locations = response.context['locations'].get_widget_data()
        self.assertEquals(len(locations.keys()), 2)
        self.assertEquals(locations.keys()[0], 'country')
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

        self.assertEquals(len(locations['city']), 0)

    def test_get_aggregates_for_a_batch(self):
        country = LocationType.objects.create(name = 'Country', slug = 'country')
        city = LocationType.objects.create(name = 'City', slug = 'city')
        village = LocationType.objects.create(name = 'Village', slug = 'village')

        uganda = Location.objects.create(name='Uganda', type = country)
        kampala = Location.objects.create(name='Kampala', tree_parent = uganda, type = city)
        abim = Location.objects.create(name='Abim', tree_parent = uganda, type = city)
        kampala_city = Location.objects.create(name='Kampala Village', tree_parent = kampala, type = village)

        batch = Batch.objects.create(order=1)
        batch_2 = Batch.objects.create(order=1)

        investigator = Investigator.objects.create(name="investigator name", mobile_number="123", location=kampala_city)
        count = 1
        while(count <= investigator_configs.NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR):
            household = Household.objects.create(investigator = investigator)
            household.batch_completed(batch_2)
            count += 1

        response = self.client.get('/aggregates/status', {'location': str(kampala.pk), 'batch': str(batch.pk)})
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(len(response.context['batches']), 2)
        self.assertEquals(response.context['batches'][0], batch)
        self.assertEquals(response.context['batches'][1], batch_2)
        self.assertEquals(response.context['selected_location'], kampala)
        self.assertEquals(response.context['selected_batch'], batch)
        self.assertEquals(response.context['households'], {'completed': 0, 'pending': 10})
        self.assertEquals(response.context['clusters'], {'completed': 0, 'pending': 1})
        self.assertEquals(len(response.context['investigators']), 1)
        self.assertEquals(response.context['investigators'][0], investigator)

        locations = response.context['locations'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

        self.assertEquals(len(locations['city']), 2)
        self.assertEquals(locations['city'][0], abim)
        self.assertEquals(locations['city'][1], kampala)

        self.assertEquals(len(locations['village']), 1)
        self.assertEquals(locations['village'][0], kampala_city)

        investigator_2 = Investigator.objects.create(name="investigator name", mobile_number="1234", location=kampala_city)
        count = 1
        while(count <= investigator_configs.NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR):
            household = Household.objects.create(investigator = investigator_2)
            household.batch_completed(batch)
            count += 1

        response = self.client.get('/aggregates/status', {'location': str(kampala.pk), 'batch': str(batch.pk)})
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(response.context['selected_location'], kampala)
        self.assertEquals(response.context['selected_batch'], batch)
        self.assertEquals(response.context['households'], {'completed': 10, 'pending': 10})
        self.assertEquals(response.context['clusters'], {'completed': 1, 'pending': 1})
        self.assertEquals(len(response.context['investigators']), 1)
        self.assertEquals(response.context['investigators'][0], investigator)

        investigator_3 = Investigator.objects.create(name="investigator name", mobile_number="12345", location=abim)
        count = 1
        while(count <= investigator_configs.NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR):
            household = Household.objects.create(investigator = investigator_3)
            household.batch_completed(batch)
            count += 1

        investigator_4 = Investigator.objects.create(name="investigator name", mobile_number="123456", location=abim)
        Household.objects.create(investigator = investigator_4).batch_completed(batch)

        response = self.client.get('/aggregates/status', {'location': str(kampala.pk), 'batch': str(batch.pk)})
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(response.context['selected_location'], kampala)
        self.assertEquals(response.context['selected_batch'], batch)
        self.assertEquals(response.context['households'], {'completed': 10, 'pending': 10})
        self.assertEquals(response.context['clusters'], {'completed': 1, 'pending': 1})
        self.assertEquals(len(response.context['investigators']), 1)
        self.assertEquals(response.context['investigators'][0], investigator)

    def test_contains_key(self):
        self.assertTrue(contains_key({'bla':'1'}, 'bla'))
        self.assertFalse(contains_key({'haha':'1'}, 'bla'))
        self.assertFalse(contains_key({'bla':'-1'}, 'bla'))
        self.assertFalse(contains_key({'bla':''}, 'bla'))
        self.assertFalse(contains_key({'bla':'NOT_A_DIGIT'}, 'bla'))

    def test_is_valid_params(self):
        self.assertTrue(is_valid({'location':'1', 'batch':'2'}))

    def test_empty_location_is_also_valid(self):
        self.assertTrue(is_valid({'location':'', 'batch':'2'}))

    def test_invalid(self):
        self.assertFalse(is_valid({'batch':'2'}))
        self.assertFalse(is_valid({'location':'2', 'batch':'NOT_A_DIGIT'}))
        self.assertFalse(is_valid({'location':'NOT_A_DIGIT', 'batch':'1'}))
        self.assertFalse(is_valid({'location':'1'}))

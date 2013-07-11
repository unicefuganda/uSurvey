from django.test import TestCase
from django.test.client import Client

from rapidsms.contrib.locations.models import Location
from survey.models import *
from survey import investigator_configs

class AggregatesPageTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_page(self):
        response = self.client.get('/aggregates/status')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/status.html', templates)

    def test_get_aggregates_for_a_batch(self):
        uganda = Location.objects.create(name='Uganda')
        abim = Location.objects.create(name='Abim', tree_parent = uganda)
        kampala = Location.objects.create(name='Kampala', tree_parent = uganda)
        kampala_city = Location.objects.create(name='Kampala City', tree_parent = kampala)
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
        self.assertEquals(response.context['selected_location'], kampala)
        self.assertEquals(response.context['selected_batch'], batch)
        self.assertEquals(response.context['households'], {'completed': 0, 'pending': 10})
        self.assertEquals(response.context['clusters'], {'completed': 0, 'pending': 1})
        self.assertEquals(len(response.context['investigators']), 1)
        self.assertEquals(response.context['investigators'][0], investigator)

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
from django.test import TestCase
from django.test.client import Client
from survey.models import *
from django.contrib.auth.models import User
from survey.investigator_configs import *
from rapidsms.contrib.locations.models import Location, LocationType

class BatchViews(TestCase):

    def setUp(self):
        self.client = Client()
        User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        self.client.login(username='Rajni', password='I_Rock')
        survey = Survey.objects.create(name = "some survey")
        self.batch = Batch.objects.create(order = 1, survey = survey, name = "Batch A")
        district = LocationType.objects.create(name=PRIME_LOCATION_TYPE, slug=PRIME_LOCATION_TYPE)
        self.kampala = Location.objects.create(name="Kampala", type=district)
        self.abim = Location.objects.create(name="Abim", type=district)
        self.batch.open_for_location(self.abim)

    def test_get_index(self):
        response = self.client.get('/batches/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/index.html', templates)
        self.assertIn(self.batch, response.context['batches'])

    def test_get_batch_view(self):
        response = self.client.get('/batches/' + str(self.batch.pk) + "/")
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/show.html', templates)
        self.assertEquals(self.batch, response.context['batch'])
        self.assertIn(self.kampala, response.context['locations'])
        self.assertIn(self.abim, response.context['open_locations'])

    def test_open_batch_for_location(self):
        self.assertFalse(self.batch.is_open_for(self.kampala))
        response = self.client.post('/batches/' + str(self.batch.pk) + "/open_to", data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)
        self.assertTrue(self.batch.is_open_for(self.kampala))

    def test_close_batch_for_location(self):
        self.assertTrue(self.batch.is_open_for(self.abim))
        response = self.client.post('/batches/' + str(self.batch.pk) + "/close_to", data={'location_id': self.abim.pk})
        self.failUnlessEqual(response.status_code, 200)
        self.assertFalse(self.batch.is_open_for(self.abim))
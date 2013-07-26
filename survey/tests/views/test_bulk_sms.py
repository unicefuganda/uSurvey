from django.test import TestCase
from django.test.client import Client
from survey.models import *
from django.contrib.auth.models import User
from survey.investigator_configs import *
from rapidsms.contrib.locations.models import Location, LocationType

class BulkSMSTest(TestCase):

    def setUp(self):
        self.client = Client()
        User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        self.client.login(username='Rajni', password='I_Rock')
        district = LocationType.objects.create(name=SEND_BULK_SMS_TO_LOCATION_TYPE, slug='district')
        country = LocationType.objects.create(name='Country', slug = 'country')
        self.kampala = Location.objects.create(name="Kampala", type=district)
        self.abim = Location.objects.create(name="Abim", type=district)
        uganda = Location.objects.create(name="Uganda", type=country)

    def test_get(self):
        response = self.client.get('/bulk_sms')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('bulk_sms/index.html', templates)
        self.assertEquals(len(response.context['locations']), 2)

    def test_send(self):
        response = self.client.post('/bulk_sms/send', data={'locations': [self.kampala.pk, self.abim.pk], 'text': 'text'})
        self.failUnlessEqual(response.status_code, 302)
        self.assertEquals(response['Location'], 'http://testserver/bulk_sms')
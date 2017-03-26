import json

from django.test.client import Client
from survey.models.locations import *
from django.contrib.auth.models import User

from survey.tests.base_test import BaseTest


class LocationTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.client = Client()
        user_without_permission = User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        self.client.login(username='useless', password='I_Suck')
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.district = LocationType.objects.create(
            name='District', parent=self.country, slug='district')
        self.city = LocationType.objects.create(
            name='City', parent=self.district, slug='city')
        self.village = LocationType.objects.create(
            name='village', parent=self.city, slug='village')
        self.uganda = Location.objects.create(name='Uganda', type=self.country)

        self.kampala = Location.objects.create(
            name='Kampala', parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(
            name='Kampala City', parent=self.kampala, type=self.city)

    def test_get_children(self):
        LocationType.objects.create(name='Village', slug='village')

        uganda = Location.objects.create(name='Uganda', type=self.country)
        kampala = Location.objects.create(
            name='Kampala', parent=uganda, type=self.city)
        abim = Location.objects.create(
            name='Abim', parent=uganda, type=self.city)
        kampala_city = Location.objects.create(
            name='Kampala City', parent=kampala, type=self.village)

        response = self.client.get('/locations/%s/children' % uganda.pk)
        self.failUnlessEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEquals(len(content), 2)

        self.assertEquals(content[0]['id'], abim.pk)
        self.assertEquals(content[0]['name'], abim.name)

        self.assertEquals(content[1]['id'], kampala.pk)
        self.assertEquals(content[1]['name'], kampala.name)

    def test_login_required(self):
        uganda = Location.objects.create(name='Uganda', type=self.country)
        self.assert_login_required('/locations/%s/children' % uganda.pk)

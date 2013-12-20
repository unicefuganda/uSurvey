import json

from django.test.client import Client
from rapidsms.contrib.locations.models import Location, LocationType
from django.contrib.auth.models import User
from survey.models import LocationTypeDetails, EnumerationArea

from survey.tests.base_test import BaseTest


class LocationTest(BaseTest):
    def setUp(self):
        self.client = Client()
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        self.client.login(username='useless', password='I_Suck')
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.city = LocationType.objects.create(name='City', slug='city')
        self.uganda = Location.objects.create(name='Uganda', type=self.country)

        self.kampala = Location.objects.create(name='Kampala', tree_parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)

    def test_get_children(self):
        LocationType.objects.create(name='Village', slug='village')

        uganda = Location.objects.create(name='Uganda', type=self.country)
        kampala = Location.objects.create(name='Kampala', tree_parent=uganda, type=self.city)
        abim = Location.objects.create(name='Abim', tree_parent=uganda, type=self.city)
        kampala_city = Location.objects.create(name='Kampala City', tree_parent=kampala, type=self.city)

        response = self.client.get('/locations/%s/children' % uganda.pk)
        self.failUnlessEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEquals(len(content), 2)

        self.assertEquals(content[0]['id'], abim.pk)
        self.assertEquals(content[0]['name'], abim.name)

        self.assertEquals(content[1]['id'], kampala.pk)
        self.assertEquals(content[1]['name'], kampala.name)

        response = self.client.get('/locations/%s/children' % kampala.pk)
        self.failUnlessEqual(response.status_code, 200)
        content = json.loads(response.content)

        self.assertEquals(len(content), 1)

        self.assertEquals(content[0]['id'], kampala_city.pk)
        self.assertEquals(content[0]['name'], kampala_city.name)

        response = self.client.get('/locations/%s/children' % kampala_city.pk)
        self.failUnlessEqual(response.status_code, 200)
        content = json.loads(response.content)

        self.assertEquals(len(content), 0)

    def test_get_enumeration_areas_data(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        bukoto = Location.objects.create(name='Bukoto', tree_parent=self.kampala_city, type=village)
        some_type = LocationType.objects.create(name='Sometype', slug='sometype')
        LocationTypeDetails.objects.create(location_type=some_type, country=self.uganda)
        kisasi = Location.objects.create(name='Kisaasi', tree_parent=bukoto, type=some_type)

        ea1 = EnumerationArea.objects.create(name="EA Kisasi1")
        ea2 = EnumerationArea.objects.create(name="EA Kisasi2")
        ea1.locations.add(kisasi)
        ea2.locations.add(kisasi)

        response = self.client.get('/locations/%s/enumeration_areas' % bukoto.pk)
        self.failUnlessEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEquals(len(content), 2)

        self.assertEquals(content[0]['id'], ea1.pk)
        self.assertEquals(content[0]['name'], ea1.name)

        self.assertEquals(content[1]['id'], ea2.pk)
        self.assertEquals(content[1]['name'], ea2.name)

    def test_login_required(self):
        uganda = Location.objects.create(name='Uganda')
        self.assert_login_required('/locations/%s/children' % uganda.pk)

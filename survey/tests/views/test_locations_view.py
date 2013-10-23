import json

from django.test.client import Client
from rapidsms.contrib.locations.models import Location, LocationType
from django.contrib.auth.models import User

from survey.tests.base_test import BaseTest


class LocationTest(BaseTest):
    def setUp(self):
        self.client = Client()
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        self.client.login(username='useless', password='I_Suck')

    def test_get_children(self):
        country = LocationType.objects.create(name = 'Country', slug = 'country')
        city = LocationType.objects.create(name = 'City', slug = 'city')
        village = LocationType.objects.create(name = 'Village', slug = 'village')

        uganda = Location.objects.create(name='Uganda', type = country)
        kampala = Location.objects.create(name='Kampala', tree_parent = uganda, type = city)
        abim = Location.objects.create(name='Abim', tree_parent = uganda, type = city)
        kampala_city = Location.objects.create(name='Kampala City', tree_parent = kampala, type = city)

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

    def test_login_required(self):
        uganda = Location.objects.create(name='Uganda')
        self.assert_login_required('/locations/%s/children' % uganda.pk)

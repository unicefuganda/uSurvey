from django.test import TestCase
from django.test.client import Client
from survey.models import *
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from survey.investigator_configs import *
from rapidsms.contrib.locations.models import Location, LocationType

class BatchViews(TestCase):

    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_batches', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)

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

    def assert_restricted_permission_for(self, url):
        self.client.logout()

        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)

        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%url, status_code=302, target_status_code=200, msg_prefix='')

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/batches/')
        self.assert_restricted_permission_for('/batches/1/')
        self.assert_restricted_permission_for('/batches/1/open_to')
        self.assert_restricted_permission_for('/batches/1/close_to')

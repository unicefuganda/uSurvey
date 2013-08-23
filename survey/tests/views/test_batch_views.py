from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from rapidsms.contrib.locations.models import Location, LocationType
from django.contrib import messages

from survey.models import *
from survey.forms.batch import BatchForm


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

        self.batch = Batch.objects.create(order = 1, name = "Batch A")
        district = LocationType.objects.create(name=PRIME_LOCATION_TYPE, slug=PRIME_LOCATION_TYPE)
        self.kampala = Location.objects.create(name="Kampala", type=district)
        city = LocationType.objects.create(name="City", slug="city")
        village = LocationType.objects.create(name="Village", slug="village")
        self.kampala_city = Location.objects.create(name="Kampala City", type=city, tree_parent=self.kampala)
        self.bukoto = Location.objects.create(name="Bukoto", type=city, tree_parent=self.kampala)
        self.kamoja = Location.objects.create(name="kamoja", type=village, tree_parent=self.bukoto)
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
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertTrue(self.batch.is_open_for(loc))

    def test_close_batch_for_location(self):
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.batch.open_for_location(loc)

        response = self.client.post('/batches/' + str(self.batch.pk) + "/close_to", data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertFalse(self.batch.is_open_for(loc))

    def assert_restricted_permission_for(self, url):
        self.client.logout()

        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)

        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%url, status_code=302, target_status_code=200, msg_prefix='')

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/batches/')
        self.assert_restricted_permission_for('/batches/new/')
        self.assert_restricted_permission_for('/batches/1/')
        self.assert_restricted_permission_for('/batches/1/open_to')
        self.assert_restricted_permission_for('/batches/1/close_to')

    def test_add_new_batch_should_load_new_template(self):
        response = self.client.get('/batches/new/')
        self.assertEqual(response.status_code,200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/new.html', templates)

    def test_batch_form_is_in_response_request_context(self):
        response = self.client.get('/batches/new/')
        self.assertIsInstance(response.context['batchform'], BatchForm)
        self.assertEqual(response.context['button_label'], 'Save')
        self.assertEqual(response.context['id'], 'add-batch-form')

    def test_post_add_new_batch_is_invalid_if_name_field_is_empty(self):
        response = self.client.post('/batches/new/', data={'name':'', 'description':''})
        self.assertTrue(len(response.context['batchform'].errors)>0)

    def test_post_add_new_batch(self):
        response = self.client.post('/batches/new/', data={'name':'Batch1', 'description':'description'})
        self.assertEqual(len(Batch.objects.filter(name='Batch1')),1)

    def test_post_add_new_batch_redirects_to_batches_table_if_valid(self):
         response = self.client.post('/batches/new/', data={'name':'Batch1', 'description':'description'})
         self.assertRedirects(response, expected_url='/batches/', status_code=302, target_status_code=200, msg_prefix='')

    def test_post_should_not_add_batch_with_existing_name(self):
        response = self.client.post('/batches/new/', data={'name':'Batch A', 'description':'description'})
        self.assertTrue(len(response.context['batchform'].errors)>0)



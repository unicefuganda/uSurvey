from django.test import TestCase
from django.test.client import Client

from rapidsms.contrib.locations.models import Location, LocationType
import json
from survey.tests.base_test import BaseTest
from survey.forms.locations import LocationTypeForm
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from mock import patch

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

class LocationTypeViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_investigators')
        self.client.login(username='Rajni', password='I_Rock')


    def test_new_should_have_location_type_form_in_response_context_for_get(self):
        response = self.client.get('/locations/type/new/')

        self.assertEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('locations/type/new.html', templates)

        self.assertIsInstance(response.context['location_type_form'], LocationTypeForm)
        self.assertEqual(response.context['button_label'], 'Create')
        self.assertEqual(response.context['title'], 'New Location Type')

    @patch('django.contrib.messages.success')
    def test_new_should_create_type_on_post(self, mock_success_message):
        form_data = {'name': 'coutryyy'}
        all_types = LocationType.objects.filter(**form_data)
        self.failIf(all_types)
        response = self.client.post('/locations/type/new/', data=form_data)
        retrieved_types = LocationType.objects.filter(**form_data)
        self.assertEquals(1, len(retrieved_types))
        assert mock_success_message.called

    def test_new_should_create_type_name_is_automatically_slugifyied_on_post(self):
        form_data = {'name': 'Country'}
        all_types = LocationType.objects.filter(**form_data)
        self.failIf(all_types)
        response = self.client.post('/locations/type/new/', data=form_data)
        retrieved_types = LocationType.objects.filter(**form_data)
        self.assertEquals(1, len(retrieved_types))
        self.assertEquals(slugify(form_data['name']), retrieved_types[0].slug)

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/locations/type/new/')

import json

from django.test import TestCase
from django.test.client import Client
from mock import *
from django.template.defaultfilters import slugify

from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import *
from survey.views.views_helper import initialize_location_type, assign_immediate_child_locations, update_location_type
from django.contrib.auth.models import User


class InvestigatorsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        self.client.login(username='Rajni', password='I_Rock')

    def assert_dictionary_equal(self, dict1,
                                dict2): # needed as QuerySet objects can't be equated -- just to not override .equals
        self.assertEquals(len(dict1), len(dict2))
        dict2_keys = dict2.keys()
        for key in dict1.keys():
            self.assertIn(key, dict2_keys)
            for index in range(len(dict1[key])):
                self.assertEquals(dict1[key][index], dict2[key][index])

    def test_new(self):
        LocationType.objects.create(name='some type', slug='some_name')
        response = self.client.get('/investigators/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/new.html', templates)
        self.assertEquals(response.context['action'], '/investigators/new/')
        self.assertEquals(response.context['id'], 'create-investigator-form')
        self.assertEquals(response.context['button_label'], 'Create Investigator')
        self.assertEquals(response.context['loading_text'], 'Creating...')


    def test_get_district_location_returns_all_locations_if_parent_not_specified(self):
        uganda = Location.objects.create(name="Uganda")
        uganda_duplicate = Location.objects.create(name="Uganda something else")
        response = self.client.get('/investigators/locations')
        self.failUnlessEqual(response.status_code, 200)
        locations = json.loads(response.content)
        self.failUnlessEqual(locations, {
            'Uganda': uganda.id,
            'Uganda something else': uganda_duplicate.id,
        })

    def test_get_district_location_returns_all_locations_if_parent_empty(self):
        uganda = Location.objects.create(name="Uganda")
        uganda_duplicate = Location.objects.create(name="Uganda something else")
        response = self.client.get('/investigators/locations?parent=')
        self.failUnlessEqual(response.status_code, 200)
        locations = json.loads(response.content)
        self.failUnlessEqual(locations, {
            'Uganda': uganda.id,
            'Uganda something else': uganda_duplicate.id,
        })


    def test_get_district_location_with_specified_parent_tree(self):
        uganda = Location.objects.create(name="Uganda")
        uganda_region = Location.objects.create(name="Uganda Region", tree_parent=uganda)
        other_location_that_is_not_child_of_uganda = Location.objects.create(name="Uganda Something else")
        response = self.client.get("/investigators/locations?parent=" + str(uganda.id))
        self.failUnlessEqual(response.status_code, 200)
        locations = json.loads(response.content)
        self.failUnlessEqual(locations, {
            'Uganda Region': uganda_region.id,
        })

    def test_get_location_failures(self):
        response = self.client.get('/investigators/locations')
        self.failUnlessEqual(response.status_code, 200)
        locations = json.loads(response.content)
        self.failUnlessEqual(locations, {})

    def test_create_investigators(self):
        country = LocationType.objects.create(name='country', slug='country')
        uganda = Location.objects.create(name="Uganda", type=country)
        backend = Backend.objects.create(name='something')
        form_data = {
            'name': 'Rajini',
            'mobile_number': '987654321',
            'male': 'f',
            'age': '20',
            'level_of_education': 'Nursery',
            'language': 'Luganda',
            'country': uganda.id,
            'location': uganda.id,
            'backend': backend.id,
            'confirm_mobile_number': '987654321',
        }
        investigator = Investigator.objects.filter(name=form_data['name'], backend = Backend.objects.create(name='something1'))
        self.failIf(investigator)
        response = self.client.post('/investigators/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 302) # ensure redirection to list investigator page
        investigator = Investigator.objects.get(name=form_data['name'])
        self.failUnless(investigator.id)
        for key in ['name', 'mobile_number', 'age', 'level_of_education', 'language']:
            value = getattr(investigator, key)
            self.assertEqual(form_data[key], str(value))

        self.assertTrue(investigator.male)
        self.assertEqual(investigator.location, uganda)
        self.assertEqual(len(investigator.households.all()), 0)

    def test_list_investigators(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=uganda, backend = Backend.objects.create(name='something'))
        response = self.client.get("/investigators/")
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)

        self.assertEqual(len(response.context['investigators']), 1)
        self.assertIn(investigator, response.context['investigators'])

        locations = response.context['location_data'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

    @patch('django.contrib.messages.error')
    def test_list_investigators_no_investigators(self, mock_error_message):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.filter(location=uganda).delete()
        response = self.client.get("/investigators/")
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)

        self.assertEqual(len(response.context['investigators']), 0)

        locations = response.context['location_data'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

        assert mock_error_message.called_once_with('There are  no investigators currently registered  for this location.')



    def test_filter_list_investigators(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        district = LocationType.objects.create(name="district", slug=slugify("district"))

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto = Location.objects.create(name="Bukoto", tree_parent=kampala)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=uganda, backend = Backend.objects.create(name='something1'))
        investigator2 = Investigator.objects.create(name="Investigator", mobile_number="987654322", location=kampala, backend = Backend.objects.create(name='something2'))
        investigator3 = Investigator.objects.create(name="Investigator", mobile_number="987654323", location=bukoto, backend = Backend.objects.create(name='something3'))

        response = self.client.get("/investigators/?location=" + str(uganda.id))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)

        self.assertEqual(len(response.context['investigators']), 3)
        for investigator in [investigator1, investigator2, investigator3]:
            self.assertIn(investigator, response.context['investigators'])

        locations = response.context['location_data'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

        self.assertEquals(len(locations['district']), 1)
        self.assertEquals(locations['district'][0], kampala)

    def test_check_mobile_number(self):
        investigator = Investigator.objects.create(name="investigator", mobile_number="123456789", backend = Backend.objects.create(name='something'))
        response = self.client.get("/investigators/check_mobile_number?mobile_number=0987654321")
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)

        response = self.client.get("/investigators/check_mobile_number?mobile_number=" + investigator.mobile_number)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

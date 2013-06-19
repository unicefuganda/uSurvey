from django.test import TestCase
from django.test.client import Client
from rapidsms.contrib.locations.models import Location
from survey.models import *
import json
import datetime
import urllib2
from survey.investigator_configs import *
from mock import *
from survey.views import *
from django.template.defaultfilters import slugify


class InvestigatorsViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.ussd_params = {
                                'transactionId': 123344,
                                'transactionTime': datetime.datetime.now().strftime('%Y%m%dT%H:%M:%S'),
                                'msisdn': '256776520831',
                                'ussdServiceCode': '130',
                                'ussdRequestString': '',
                                'response': False
                            }

    def assert_dictionary_equal(self, dict1, dict2): # needed as QuerySet objects can't be equated -- just to not override .equals
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
        templates = [ template.name for template in response.templates]
        self.assertIn('investigators/new.html', templates)

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
        uganda_region = Location.objects.create(name="Uganda Region", tree_parent = uganda)
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
        form_data = {
                        'name': 'Rajini',
                        'mobile_number': '987654321',
                        'male': 'f',
                        'age': '20',
                        'level_of_education': 'Nursery',
                        'language': 'Luganda',
                        'country':uganda.id,
                        'location': uganda.id,
                        'confirm_mobile_number': '987654321',
                    }
        investigator = Investigator.objects.filter(name=form_data['name'])
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
        self.assertEqual(len(investigator.households.all()), 1)

    @patch('rapidsms.contrib.locations.models.LocationType.objects.all')
    def test_initialize_location_type(self, mock_location_type):
        some_type = MagicMock()
        some_type.name='some type'
        mock_location_type.return_value = [some_type]
        ltype = initialize_location_type(default_select='HAHA')
        self.assertEquals(ltype['some type']['value'], '')
        self.assertEquals(ltype['some type']['text'], 'HAHA')
        self.assertEquals(len(ltype['some type']['siblings']), 0)

    def test_assign_immediate_child_locations(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        district = LocationType.objects.create(name="district", slug=slugify("district"))

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        kabale = Location.objects.create(name="Kabale", type=district, tree_parent=uganda)

        selected_location = initialize_location_type(default_select='HOHO')
        self.assert_dictionary_equal(selected_location['country'], {'text': 'HOHO', 'value': '', 'siblings': [uganda]})
        self.assert_dictionary_equal(selected_location['district'], {'text': 'HOHO', 'value': '', 'siblings': []})

        selected_location = assign_immediate_child_locations(selected_location=selected_location, location=uganda)
        self.assert_dictionary_equal(selected_location['country'], {'text': 'HOHO', 'value': '', 'siblings': [uganda]})
        self.assert_dictionary_equal(selected_location['district'], {'text': 'HOHO', 'value': '', 'siblings': [kabale, kampala]})

    def test_update_location_type(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda", type=country)

        region = LocationType.objects.create(name="region", slug=slugify("region"))
        central = Location.objects.create(name="Central", type=region, tree_parent=uganda)

        district = LocationType.objects.create(name="district", slug=slugify("district"))
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=central)
        kampala_sibling = Location.objects.create(name="Kampala Sibling", type=district, tree_parent=central)

        county = LocationType.objects.create(name="county", slug=slugify("county"))

        selected_location = initialize_location_type()
        selected_location = update_location_type(selected_location, kampala.id)

        self.assertEquals(selected_location['country'], { 'value': uganda.id, 'text': u'Uganda', 'siblings': [{'id': '', 'name': ''}]  })
        self.assertEquals(selected_location['region'], {'value':  central.id ,'text': central.name, 'siblings': [{'id': '', 'name': ''}]})
        self.assertEquals(selected_location['district'], {'value':  kampala.id ,'text': kampala.name, 'siblings': [{'id': '', 'name': ''}, kampala_sibling]})
        self.assertEquals(selected_location['county'], {'value':  '' ,'text': '', 'siblings': []})

    def test_update_location_type_no_location_given(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        selected_location_orig = initialize_location_type()
        selected_location = update_location_type(selected_location=selected_location_orig, location_id='')
        self.assertEquals(selected_location_orig, selected_location)

    def test_list_investigators(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=uganda)
        response = self.client.get("/investigators/")
        self.failUnlessEqual(response.status_code, 200)
        templates = [ template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)

        self.assertEqual(len(response.context['investigators']), 1)
        self.assertIn(investigator, response.context['investigators'])
        self.assertEquals(len(response.context['location_type']), 1)
        self.assert_dictionary_equal({ 'value': '', 'text':'All', 'siblings': [uganda]}, response.context['location_type'][country.name])

    def test_filter_list_investigators(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        district = LocationType.objects.create(name="district", slug=slugify("district"))

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type= district, tree_parent=uganda)
        bukoto = Location.objects.create(name="Bukoto", tree_parent=kampala)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=uganda)
        investigator2 = Investigator.objects.create(name="Investigator", mobile_number="987654322", location=kampala)
        investigator3 = Investigator.objects.create(name="Investigator", mobile_number="987654323", location=bukoto)

        response = self.client.get("/investigators/filter/"+ str(uganda.id)+"/")
        self.failUnlessEqual(response.status_code, 200)
        templates = [ template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)
        
        self.assertEquals(response.context['selected_location_type'], 'country')
        
        self.assertEqual(len(response.context['investigators']), 3)
        for investigator in [investigator1, investigator2, investigator3]:
          self.assertIn(investigator, response.context['investigators'])

        self.assertEqual(len(response.context['location_type']), 2)
        self.assertEquals({ 'value': uganda.id, 'text':uganda.name, 'siblings': [{'id': '', 'name': 'All'}]}, response.context['location_type'][country.name])
        self.assert_dictionary_equal({ 'value': '', 'text':'All', 'siblings': [kampala]}, response.context['location_type'][district.name])

    def test_check_mobile_number(self):
        investigator = Investigator.objects.create(name="investigator", mobile_number="123456789")
        response = self.client.get("/investigators/check_mobile_number?mobile_number=0987654321")
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)

        response = self.client.get("/investigators/check_mobile_number?mobile_number=" + investigator.mobile_number)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

    def test_ussd_url(self):
        response_message = "responseString=%s&action=end" % USSD.MESSAGES['USER_NOT_REGISTERED']
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

        response = self.client.get('/ussd/', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

        client = Client(enforce_csrf_checks=True)
        response = self.client.post('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

        response = self.client.post('/ussd/', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(urllib2.unquote(response.content), response_message)

    def test_ussd_simulator(self):
        response = self.client.get('/ussd/simulator')
        self.failUnlessEqual(response.status_code, 200)
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

    def test_new(self):
        response = self.client.get('/investigators/new')
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
        uganda = Location.objects.create(name="Uganda")
        form_data = {
                        'name': 'Rajini',
                        'mobile_number': '9876543210',
                        'male': 'f',
                        'age': '20',
                        'level_of_education': 'Nursery',
                        'language': 'Luganda',
                        'location': uganda.id
                    }
        investigator = Investigator.objects.filter(name=form_data['name'])
        self.failIf(investigator)
        response = self.client.post('/investigators/', data=form_data)
        self.failUnlessEqual(response.status_code, 201)
        investigator = Investigator.objects.get(name=form_data['name'])
        self.failUnless(investigator.id)
        for key in ['name', 'mobile_number', 'age', 'level_of_education', 'language']:
            value = getattr(investigator, key)
            self.assertEqual(form_data[key], str(value))

        self.assertTrue(investigator.male)
        self.assertEqual(investigator.location, uganda)

    @patch('rapidsms.contrib.locations.models.LocationType.objects.all')
    def test_initialize_location_type(self, mock_location_type):
      some_type = MagicMock()
      some_type.name='some type'
      mock_location_type.return_value = [some_type]
      ltype = initialize_location_type()
      self.assertEquals(ltype['some type'], {'value': '','text':'All', 'siblings': []})

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

      # self.assertDictEqual(selected_location['country'], {'siblings': [], 'text': u'Uganda', 'value': 20})
      # self.assertEquals(selected_location['region'], {'value':  central.id ,'text': central.name, 'siblings': []})
      # self.assertEquals(selected_location['district'], {'value':  kampala.id ,'text': kampala.name, 'siblings': [kampala_sibling]})
      # self.assertEquals(selected_location['county'], {'value':  '' ,'text': 'All', 'siblings': []})

    def test_list_investigators(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210", location=uganda)
        response = self.client.get("/investigators/")
        self.failUnlessEqual(response.status_code, 200)
        templates = [ template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)

        self.assertEqual(len(response.context['investigators']), 1)
        self.assertIn(investigator, response.context['investigators'])

        self.assertEqual(len(response.context['location_type']), 1)
        self.assertEquals({ 'value': '', 'text':'All', 'siblings': []}, response.context['location_type'][country.name])

    def test_filter_list_investigators(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210", location=uganda)
        response = self.client.get("/investigators/filter/"+ str(uganda.id)+"/")
        self.failUnlessEqual(response.status_code, 200)
        templates = [ template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)

        self.assertEqual(len(response.context['investigators']), 1)
        self.assertIn(investigator, response.context['investigators'])

        self.assertEqual(len(response.context['location_type']), 1)


    def test_check_mobile_number(self):
        investigator = Investigator.objects.create(name="investigator", mobile_number="1234567890")
        response = self.client.get("/investigators/check_mobile_number?mobile_number=0987654321")
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)

        response = self.client.get("/investigators/check_mobile_number?mobile_number=" + investigator.mobile_number)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

    def test_ussd_url(self):
        response = self.client.get('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 404)

        response = self.client.get('/ussd/', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 404)

        client = Client(enforce_csrf_checks=True)
        response = self.client.post('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 404)

        response = self.client.post('/ussd/', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 404)

    def test_ussd_non_registered_user(self):
        response = self.client.post('/ussd', data=self.ussd_params)
        self.failUnlessEqual(response.status_code, 404)

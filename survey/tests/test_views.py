from django.test import TestCase
from django.test.client import Client
from rapidsms.contrib.locations.models import Location
from survey.models import *
import json

class InvestigatorsViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_new(self):
        response = self.client.get('/investigators/new')
        self.failUnlessEqual(response.status_code, 200)
        templates = [ template.name for template in response.templates]
        self.assertIn('investigators/new.html', templates)

    def test_get_location(self):
        uganda = Location.objects.create(name="Uganda")
        uganda_region = Location.objects.create(name="Uganda Region", tree_parent = uganda)
        uganda_duplicate = Location.objects.create(name="Uganda something else")
        response = self.client.get('/investigators/locations?q=uga')
        self.failUnlessEqual(response.status_code, 200)
        locations = json.loads(response.content)
        self.failUnlessEqual(locations, {
                                            'Uganda': uganda.id,
                                            'Uganda Region, Uganda': uganda_region.id,
                                            'Uganda something else': uganda_duplicate.id,
                                        })

    def test_get_location_failures(self):
        response = self.client.get('/investigators/locations?q=uga')
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
        response = self.client.post('/investigators', data=form_data)
        self.failUnlessEqual(response.status_code, 201)
        investigator = Investigator.objects.get(name=form_data['name'])
        self.failUnless(investigator.id)
        for key in ['name', 'mobile_number', 'age', 'level_of_education', 'language']:
            value = getattr(investigator, key)
            self.assertEqual(form_data[key], str(value))

        self.assertTrue(investigator.male)
        self.assertEqual(investigator.location, uganda)
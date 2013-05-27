from django.test import TestCase
from survey.forms import *
from rapidsms.contrib.locations.models import Location, LocationType

class InvestigatorFormTest(TestCase):

    def setUp(self):
        country = LocationType.objects.create(name='Country',slug='country')
        district = LocationType.objects.create(name='District',slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        self.location = kampala

    def test_valid(self):
        form_data = {
                        'name': 'Rajini',
                        'mobile_number': '9876543210',
                        'male': 't',
                        'age': '20',
                        'level_of_education': 'Primary',
                        'location': self.location.id,
                        'language': 'Luganda',
                        'id': 200
                    }
        investigator_form = InvestigatorForm(form_data)
        self.assertTrue(investigator_form.is_valid())
        investigator = investigator_form.save()
        self.failUnless(investigator.id)
        self.assertNotEqual(investigator.id, form_data['id'])

    def test_invalid(self):
        form_data = {
                        'name': 'Rajini',
                        'mobile_number': '9876543210',
                        'male': 't',
                        'age': '20',
                        'level_of_education': 'HSC',
                        'language': 'Luganda',
                        'location': self.location.id
                    }
        for key in ['name', 'mobile_number','age', 'level_of_education', 'location']:
            modified_form_data = dict(form_data.copy())
            modified_form_data[key] = None
            print modified_form_data
            investigator_form = InvestigatorForm(modified_form_data)
            self.assertFalse(investigator_form.is_valid())

    def test_langugage_and_level_of_education_validity(self):
        for key in ['language', 'level_of_education']:
            investigator = InvestigatorForm({key: 'something'})
            self.assertEqual(investigator.errors[key][0], 'Select a valid choice. something is not one of the available choices.')
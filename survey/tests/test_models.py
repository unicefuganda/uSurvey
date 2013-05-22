from django.test import TestCase
from survey.models import *
from django.db import IntegrityError
from rapidsms.contrib.locations.models import Location, LocationType


class InvestigatorTest(TestCase):

    def test_fields(self):
        investigator = Investigator()
        fields = [str(item.attname) for item in investigator._meta.fields]
        print fields
        self.assertEqual(len(fields), 9)
        for field in ['id', 'name', 'mobile_number', 'created', 'modified', 'male', 'age', 'level_of_education', 'location_id']:
            self.assertIn(field, fields)

    def test_store(self):
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210")
        self.failUnless(investigator.id)
        self.failUnless(investigator.created)
        self.failUnless(investigator.modified)

    def test_validations(self):
        Investigator.objects.create(name="", mobile_number = "mobile_number")
        self.failUnlessRaises(IntegrityError, Investigator.objects.create, mobile_number = "mobile_number")

class LocationTest(TestCase):

    def test_store(self):
        country = LocationType.objects.create(name='Country',slug='country')
        district = LocationType.objects.create(name='District',slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)

        u = Location.objects.get(type__name='Country',name='Uganda')
        report_locations = u.get_descendants(include_self=True).all()
        self.assertEqual(len(report_locations), 2)
        self.assertIn(uganda, report_locations)
        self.assertIn(kampala, report_locations)
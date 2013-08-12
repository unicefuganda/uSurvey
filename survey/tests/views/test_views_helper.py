from django.test import TestCase

from rapidsms.contrib.locations.models import Location, LocationType

class LocationViewFilterTest(TestCase):
    def test_true(self):
        self.assertTrue(True)
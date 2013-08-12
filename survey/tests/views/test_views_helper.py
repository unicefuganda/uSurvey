from django.test import TestCase

from rapidsms.contrib.locations.models import Location, LocationType
from survey.views.views_helper import contains_key

class ViewsHelperTest(TestCase):
    def test_contains_key(self):
        self.assertTrue(contains_key({'bla':'1'}, 'bla'))
        self.assertFalse(contains_key({'haha':'1'}, 'bla'))
        self.assertFalse(contains_key({'bla':'-1'}, 'bla'))
        self.assertFalse(contains_key({'bla':''}, 'bla'))
        self.assertFalse(contains_key({'bla':'NOT_A_DIGIT'}, 'bla'))

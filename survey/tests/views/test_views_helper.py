from django.test import TestCase

from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import LocationTypeDetails
from survey.views.views_helper import contains_key, get_descendants

class ViewsHelperTest(TestCase):
    def test_contains_key(self):
        self.assertTrue(contains_key({'bla':'1'}, 'bla'))
        self.assertFalse(contains_key({'haha':'1'}, 'bla'))
        self.assertFalse(contains_key({'bla':'-1'}, 'bla'))
        self.assertFalse(contains_key({'bla':''}, 'bla'))
        self.assertFalse(contains_key({'bla':'NOT_A_DIGIT'}, 'bla'))

    def test_get_descendants(self):
        country = LocationType.objects.create(name='Country', slug='country')
        region = LocationType.objects.create(name='Region', slug='region')
        city = LocationType.objects.create(name='City', slug='city')
        parish = LocationType.objects.create(name='Parish', slug='parish')
        village = LocationType.objects.create(name='Village', slug='village')
        subcounty = LocationType.objects.create(name='Subcounty', slug='subcounty')

        africa = Location.objects.create(name='Africa', type=country)
        LocationTypeDetails.objects.create(country=africa, location_type=country)
        LocationTypeDetails.objects.create(country=africa, location_type=region)
        LocationTypeDetails.objects.create(country=africa, location_type=city)
        LocationTypeDetails.objects.create(country=africa, location_type=parish)
        LocationTypeDetails.objects.create(country=africa, location_type=village)
        LocationTypeDetails.objects.create(country=africa, location_type=subcounty)

        uganda = Location.objects.create(name='Uganda', type=region, tree_parent=africa)

        abim = Location.objects.create(name='ABIM', tree_parent=uganda, type=city)

        abim_son = Location.objects.create(name='LABWOR', tree_parent=abim, type=parish)

        abim_son_son = Location.objects.create(name='KALAKALA', tree_parent=abim_son, type=village)
        abim_son_daughter = Location.objects.create(name='OYARO', tree_parent=abim_son, type=village)

        abim_son_daughter_daughter = Location.objects.create(name='WIAWER', tree_parent=abim_son_daughter, type=subcounty)

        abim_son_son_daughter = Location.objects.create(name='ATUNGA', tree_parent=abim_son_son, type=subcounty)
        abim_son_son_son = Location.objects.create(name='WICERE', tree_parent=abim_son_son, type=subcounty)

        expected_location_descendants = [abim, abim_son, abim_son_son, abim_son_daughter, abim_son_son_daughter,
                                         abim_son_son_son, abim_son_daughter_daughter]

        self.assertItemsEqual(expected_location_descendants, get_descendants(abim))

    def test_get_descendants_when_include_self_is_false(self):
        country = LocationType.objects.create(name='Country', slug='country')
        region = LocationType.objects.create(name='Region', slug='region')
        city = LocationType.objects.create(name='City', slug='city')
        parish = LocationType.objects.create(name='Parish', slug='parish')
        village = LocationType.objects.create(name='Village', slug='village')
        subcounty = LocationType.objects.create(name='Subcounty', slug='subcounty')

        africa = Location.objects.create(name='Africa', type=country)
        LocationTypeDetails.objects.create(country=africa, location_type=country)
        LocationTypeDetails.objects.create(country=africa, location_type=region)
        LocationTypeDetails.objects.create(country=africa, location_type=city)
        LocationTypeDetails.objects.create(country=africa, location_type=parish)
        LocationTypeDetails.objects.create(country=africa, location_type=village)
        LocationTypeDetails.objects.create(country=africa, location_type=subcounty)

        uganda = Location.objects.create(name='Uganda', type=region, tree_parent=africa)

        abim = Location.objects.create(name='ABIM', tree_parent=uganda, type=city)

        abim_son = Location.objects.create(name='LABWOR', tree_parent=abim, type=parish)

        abim_son_son = Location.objects.create(name='KALAKALA', tree_parent=abim_son, type=village)
        abim_son_daughter = Location.objects.create(name='OYARO', tree_parent=abim_son, type=village)

        abim_son_daughter_daughter = Location.objects.create(name='WIAWER', tree_parent=abim_son_daughter, type=subcounty)

        abim_son_son_daughter = Location.objects.create(name='ATUNGA', tree_parent=abim_son_son, type=subcounty)
        abim_son_son_son = Location.objects.create(name='WICERE', tree_parent=abim_son_son, type=subcounty)

        expected_location_descendants = [abim_son, abim_son_son, abim_son_daughter, abim_son_son_daughter,
                                         abim_son_son_son, abim_son_daughter_daughter]

        descendants = get_descendants(abim, include_self=False)
        self.assertItemsEqual(expected_location_descendants, descendants)
        self.assertNotIn(abim, expected_location_descendants, descendants)


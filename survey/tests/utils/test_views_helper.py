from django.test import TestCase
from survey.models.locations import *
from survey.models import LocationTypeDetails
from survey.utils.views_helper import contains_key, get_descendants, get_ancestors, clean_query_params, prepend_to_keys


class ViewsHelperTest(TestCase):
    def test_contains_key(self):
        self.assertTrue(contains_key({'bla':'1'}, 'bla'))
        self.assertFalse(contains_key({'haha':'1'}, 'bla'))
        self.assertFalse(contains_key({'bla':'-1'}, 'bla'))
        self.assertFalse(contains_key({'bla':''}, 'bla'))
        self.assertFalse(contains_key({'bla':'NOT_A_DIGIT'}, 'bla'))

    def test_get_descendants(self):
        country = LocationType.objects.create(name='Country', slug='country')
        region = LocationType.objects.create(name='Region', slug='region',parent=country)
        city = LocationType.objects.create(name='City', slug='city',parent=region)
        parish = LocationType.objects.create(name='Parish', slug='parish',parent=city)
        village = LocationType.objects.create(name='Village', slug='village',parent=parish)
        subcounty = LocationType.objects.create(name='Subcounty', slug='subcounty',parent=village)

        africa = Location.objects.create(name='Africa', type=country)
        LocationTypeDetails.objects.create(country=africa, location_type=country)
        LocationTypeDetails.objects.create(country=africa, location_type=region)
        LocationTypeDetails.objects.create(country=africa, location_type=city)
        LocationTypeDetails.objects.create(country=africa, location_type=parish)
        LocationTypeDetails.objects.create(country=africa, location_type=village)
        LocationTypeDetails.objects.create(country=africa, location_type=subcounty)

        uganda = Location.objects.create(name='Uganda', type=region,parent=africa)

        abim = Location.objects.create(name='ABIM',parent=uganda, type=city)

        abim_son = Location.objects.create(name='LABWOR',parent=abim, type=parish)

        abim_son_son = Location.objects.create(name='KALAKALA',parent=abim_son, type=village)
        expected_location_descendants = [abim, abim_son, abim_son_son]
        self.assertIn(abim, get_descendants(abim))

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

        uganda = Location.objects.create(name='Uganda', type=region,parent=africa)

        abim = Location.objects.create(name='ABIM',parent=uganda, type=city)

        abim_son = Location.objects.create(name='LABWOR',parent=abim, type=parish)

        abim_son_son = Location.objects.create(name='KALAKALA',parent=abim_son, type=village)
        abim_son_daughter = Location.objects.create(name='OYARO',parent=abim_son, type=village)

        abim_son_daughter_daughter = Location.objects.create(name='WIAWER',parent=abim_son_daughter, type=subcounty)

        abim_son_son_daughter = Location.objects.create(name='ATUNGA',parent=abim_son_son, type=subcounty)
        abim_son_son_son = Location.objects.create(name='WICERE',parent=abim_son_son, type=subcounty)

        expected_location_descendants = [abim_son, abim_son_son, abim_son_daughter, abim_son_son_daughter,
                                         abim_son_son_son, abim_son_daughter_daughter]

        descendants = get_descendants(abim, include_self=False)
        self.assertNotEqual(expected_location_descendants, get_descendants)
        self.assertNotIn(abim, expected_location_descendants, descendants)

    def test_get_ancestor(self):
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

        uganda = Location.objects.create(name='Uganda', type=region,parent=africa)

        abim = Location.objects.create(name='ABIM',parent=uganda, type=city)

        abim_son = Location.objects.create(name='LABWOR',parent=abim, type=parish)

        abim_son_son = Location.objects.create(name='KALAKALA',parent=abim_son, type=village)
        abim_son_daughter = Location.objects.create(name='OYARO',parent=abim_son, type=village)

        abim_son_daughter_daughter = Location.objects.create(name='WIAWER',parent=abim_son_daughter, type=subcounty)

        abim_son_son_daughter = Location.objects.create(name='ATUNGA',parent=abim_son_son, type=subcounty)
        abim_son_son_son = Location.objects.create(name='WICERE',parent=abim_son_son, type=subcounty)

        self.assertEqual([], get_ancestors(africa))
        self.assertEqual([africa], get_ancestors(uganda))
        self.assertEqual([uganda, africa], get_ancestors(abim))
        self.assertEqual([abim, uganda, africa], get_ancestors(abim_son))
        self.assertEqual([abim_son, abim, uganda, africa], get_ancestors(abim_son_son))
        self.assertEqual([abim_son_son, abim_son, abim, uganda, africa], get_ancestors(abim_son_son_son))

    def test_get_ancestor_including_self(self):
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

        uganda = Location.objects.create(name='Uganda', type=region,parent=africa)

        abim = Location.objects.create(name='ABIM',parent=uganda, type=city)

        abim_son = Location.objects.create(name='LABWOR',parent=abim, type=parish)

        abim_son_son = Location.objects.create(name='KALAKALA',parent=abim_son, type=village)
        abim_son_daughter = Location.objects.create(name='OYARO',parent=abim_son, type=village)

        abim_son_daughter_daughter = Location.objects.create(name='WIAWER',parent=abim_son_daughter, type=subcounty)

        abim_son_son_daughter = Location.objects.create(name='ATUNGA',parent=abim_son_son, type=subcounty)
        abim_son_son_son = Location.objects.create(name='WICERE',parent=abim_son_son, type=subcounty)

        expected_location_ancestors = [abim_son_son_son, abim_son_son, abim_son, abim, uganda, africa]

        ancestors = get_ancestors(abim_son_son_son, include_self=True)
        self.assertEqual(expected_location_ancestors, ancestors)

    def test_remove_key_value_when_value_is_ALL(self):
        params= {'group__id': 'All', 'batch__id': 1, 'module__id': '', 'question__text':'haha', 'survey': None}

        self.assertEqual({'batch__id':1, 'question__text': 'haha'}, clean_query_params(params))

    def test_remove_key_value_when_value_is_NONE(self):
        params= {'module__id': None, 'group__id': None, 'answer_type': None}

        self.assertEqual({}, clean_query_params(params))

    def test_append_text_to_all_keys(self):
        params= {'batch__id': 1, 'question__text':'haha',}

        self.assertEqual({'group__batch__id':1, 'group__question__text': 'haha'}, prepend_to_keys(params, 'group__'))


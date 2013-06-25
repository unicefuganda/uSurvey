from django.test import TestCase
from mock import *
from django.template.defaultfilters import slugify

from rapidsms.contrib.locations.models import Location, LocationType
from survey.views.location_filter_helper import initialize_location_type, assign_immediate_child_locations, update_location_type


class LocationViewFilterTest(TestCase):
    def assert_dictionary_equal(self, dict1, dict2): # needed as QuerySet objects can't be equated -- just to not override .equals
        self.assertEquals(len(dict1), len(dict2))
        dict2_keys = dict2.keys()
        for key in dict1.keys():
            self.assertIn(key, dict2_keys)
            for index in range(len(dict1[key])):
                self.assertEquals(dict1[key][index], dict2[key][index])

    @patch('rapidsms.contrib.locations.models.LocationType.objects.all')
    def test_initialize_location_type(self, mock_location_type):
        some_type = MagicMock()
        some_type.name = 'some type'
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
        self.assert_dictionary_equal(selected_location['district'],
                                     {'text': 'HOHO', 'value': '', 'siblings': [kabale, kampala]})

    def test_update_location_type(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda", type=country)

        region = LocationType.objects.create(name="region", slug=slugify("region"))
        central = Location.objects.create(name="Central", type=region, tree_parent=uganda)

        district = LocationType.objects.create(name="district", slug=slugify("district"))
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=central)
        kampala_sibling = Location.objects.create(name="Kampala Sibling", type=district, tree_parent=central)

        county = LocationType.objects.create(name="county", slug=slugify("county"))

        selected_location = initialize_location_type(default_select='')
        selected_location = update_location_type(selected_location, kampala.id)

        self.assertEquals(selected_location['country'],
                          {'value': uganda.id, 'text': u'Uganda', 'siblings': [{'id': '', 'name': ''}]})
        self.assertEquals(selected_location['region'],
                          {'value': central.id, 'text': central.name, 'siblings': [{'id': '', 'name': ''}]})
        self.assertEquals(selected_location['district'], {'value': kampala.id, 'text': kampala.name,
                                                          'siblings': [{'id': '', 'name': ''}, kampala_sibling]})
        self.assertEquals(selected_location['county'], {'value': '', 'text': '', 'siblings': []})

    def test_update_location_type_no_location_given(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        selected_location_orig = initialize_location_type(default_select='')
        selected_location = update_location_type(selected_location=selected_location_orig, location_id='')
        self.assertEquals(selected_location_orig, selected_location)

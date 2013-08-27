from django.test import TestCase
from survey.templatetags.template_tags import *


class TemplateTagsTest(TestCase):

    def test_gets_key_value_from_location_dict(self):
        country_name = 'Uganda'
        district_name = 'Kampala'
        county_name = 'Bukoto'

        location_dict = {'Country': country_name, 'District': district_name, 'County': county_name}

        self.assertEqual(get_location(location_dict, 'Country'), country_name)
        self.assertEqual(get_location(location_dict, 'District'), district_name)
        self.assertEqual(get_location(location_dict, 'County'), county_name)

    def test_returns_empty_string_if_key_does_not_exist_from_location_dict(self):
        country_name = 'Uganda'
        district_name = 'Kampala'

        location_dict = {'Country': country_name, 'District': district_name}

        self.assertEqual(get_location(location_dict, 'Country'), country_name)
        self.assertEqual(get_location(location_dict, 'District'), district_name)
        self.assertEqual(get_location(location_dict, 'County'), "")

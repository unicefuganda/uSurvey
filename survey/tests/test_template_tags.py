from datetime import date
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

    def test_should_know_how_to_format_date(self):
        date_entered = date(2008, 4, 5)
        date_expected = "Apr 05, 2008"
        self.assertEqual(format_date(date_entered), date_expected)

    def test_shoud_return_months_given_month_number(self):
        self.assertEqual('January', get_month(0))
        self.assertEqual('March', get_month(2))
        self.assertEqual('N/A', get_month(None))
        self.assertEqual('N/A', get_month(''))

    def test_should_return_url_given_url_name(self):
        self.assertEqual('/surveys/', get_url('survey_list_page'))
        self.assertEqual('/surveys/1/delete/', get_url('delete_survey', 1))
        self.assertEqual('/surveys/1/batches/2/', get_url('batch_show_page', "1, 2"))
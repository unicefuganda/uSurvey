from datetime import date
from django.test import TestCase
from survey.models import Batch, Survey
from survey.templatetags.template_tags import *


class TemplateTagsTest(TestCase):

    def test_modulo_understands_number_is_modulo_of_another(self):
        self.assertTrue(modulo(4, 2))

    def test_modulo_understands_number_is_not_modulo_of_another(self):
        self.assertFalse(modulo(4, 3))

    def test_knows_mobile_number_not_in_field_string(self):
        self.assertFalse(is_mobile_number(""))

    def test_knows_mobile_number_in_field_string(self):
        self.assertTrue(is_mobile_number("mobile number : 1234567"))

    def test_gets_key_value_from_location_dict(self):
        country_name = 'Uganda'
        district_name = 'Kampala'
        county_name = 'Bukoto'

        location_dict = {'Country': country_name, 'District': district_name, 'County': county_name}

        self.assertEqual(get_value(location_dict, 'Country'), country_name)
        self.assertEqual(get_value(location_dict, 'District'), district_name)
        self.assertEqual(get_value(location_dict, 'County'), county_name)

    def test_returns_empty_string_if_key_does_not_exist_from_location_dict(self):
        country_name = 'Uganda'
        district_name = 'Kampala'

        location_dict = {'Country': country_name, 'District': district_name}

        self.assertEqual(get_value(location_dict, 'Country'), country_name)
        self.assertEqual(get_value(location_dict, 'District'), district_name)
        self.assertEqual(get_value(location_dict, 'County'), "")

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
        self.assertEqual('/surveys/', get_url_without_ids('survey_list_page'))

    def test_should_return_url_given_url_name_and_ids(self):    
        self.assertEqual('/surveys/1/delete/', get_url_with_ids( 1, 'delete_survey'))
        self.assertEqual('/surveys/1/batches/2/', get_url_with_ids("1, 2", 'batch_show_page'))

    def test_should_return_concatenated_ints_in_a_single_string(self):    
        self.assertEqual('1, 2', add_string(1,2))
        self.assertEqual('1, 2', add_string('1','2'))

    def test_should_return_repeated_string(self):
        self.assertEqual('000', repeat_string('0', 4))

    def test_should_return_selected_for_selected_batch(self):
        survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        batch = Batch.objects.create(name="open survey", survey=survey)
        self.assertEqual("selected='selected'", is_survey_selected_given(survey, batch))

    def test_should_return_none_for_selected_batch(self):
        survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        batch = Batch.objects.create(name="Batch not belonging to survey")
        self.assertIsNone(is_survey_selected_given(survey, batch))

    def test_should_return_none_if_selected_batch_has_no_survey(self):
        survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        batch = Batch.objects.create(name="Batch not belonging to survey")
        self.assertIsNone(is_survey_selected_given(survey, batch))

    def test_should_return_none_when_selected_batch_is_none(self):
        survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        self.assertIsNone(is_survey_selected_given(survey, None))
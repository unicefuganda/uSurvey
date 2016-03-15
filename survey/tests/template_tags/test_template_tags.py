from datetime import date
from django.test import TestCase
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import Batch, Survey, LocationTypeDetails, EnumerationArea
from survey.templatetags.template_tags import *
from survey.views.location_widget import LocationWidget
from survey.models.locations import *

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

    def test_knows_batch_is_activated_for_non_response_for_location(self):
        country = LocationType.objects.create(name="Country", slug='country')
        district = LocationType.objects.create(name="District", parent=country,slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, parent=uganda)
        # Location.objects.create(name="Kampala")

        all_open_locations = Location.objects.all()
        self.assertEqual("checked='checked'", non_response_is_activefor(all_open_locations, kampala))

    def test_knows_batch_is_not_activated_for_non_response_for_location(self):
        country = LocationType.objects.create(name="Country", slug='country')
        district = LocationType.objects.create(name="District", parent=country,slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, parent=uganda)
      #  kampala = Location.objects.create(name="Kampala")
       # Location.objects.create(name="Mbarara")

        all_open_locations = Location.objects.filter(name="Mbarara")
        self.assertEqual(None, non_response_is_activefor(all_open_locations, kampala))

    def setUp(self):
        locate = LocationType.objects.create( )

    def test_knows_ea_is_selected_given_location_data(self):
        country = LocationType.objects.create(name="Country", slug='country')
        district = LocationType.objects.create(name="District", parent=country,slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)

        kisasi = Location.objects.create(name='Kisaasi',type=district,parent=uganda)

        ea1 = EnumerationArea.objects.create(name="EA Kisasi1")
        ea2 = EnumerationArea.objects.create(name="EA Kisasi2")
        ea1.locations.add(kisasi)
        ea2.locations.add(kisasi)

        location_widget = LocationWidget(selected_location=kisasi, ea=ea1)

        self.assertEqual("selected='selected'", is_ea_selected(location_widget, ea1))
        self.assertIsNone(is_ea_selected(location_widget, ea2))

    def test_ancestors_reversed_reversed(self):
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

        uganda = Location.objects.create(name='Uganda', type=region, parent=africa)

        abim = Location.objects.create(name='ABIM', parent=uganda, type=city)

        abim_son = Location.objects.create(name='LABWOR', parent=abim, type=parish)

        abim_son_son = Location.objects.create(name='KALAKALA', parent=abim_son, type=village)
        abim_son_daughter = Location.objects.create(name='OYARO', parent=abim_son, type=village)

        abim_son_daughter_daughter = Location.objects.create(name='WIAWER', parent=abim_son_daughter, type=subcounty)

        abim_son_son_daughter = Location.objects.create(name='ATUNGA', parent=abim_son_son, type=subcounty)
        abim_son_son_son = Location.objects.create(name='WICERE', parent=abim_son_son, type=subcounty)

        self.assertEqual([], ancestors_reversed(africa))
        self.assertEqual([africa], ancestors_reversed(uganda))
        self.assertEqual([africa, uganda], ancestors_reversed(abim))
        self.assertEqual([africa, uganda, abim], ancestors_reversed(abim_son))
        self.assertEqual([africa, uganda, abim, abim_son], ancestors_reversed(abim_son_son))
        self.assertEqual([africa, uganda, abim, abim_son, abim_son_son], ancestors_reversed(abim_son_son_son))
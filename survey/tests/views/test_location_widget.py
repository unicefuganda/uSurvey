from random import randint
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import LocationTypeDetails, EnumerationArea
from survey.tests.base_test import BaseTest
from survey.views.location_widget import LocationWidget


class LocationWidgetTest(BaseTest):

    def setUp(self):
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.city = LocationType.objects.create(name='City', slug='city')
        self.uganda = Location.objects.create(name='Uganda', type=self.country)

        self.kampala = Location.objects.create(name='Kampala', tree_parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)
        ea = EnumerationArea.objects.create(name="Uganda EA")
        ea.locations.add(self.kampala_city)

        self.generate_location_type_details(self.uganda, the_country=self.uganda)
        self.country_type_details = LocationTypeDetails.objects.get(location_type=self.country, country=self.uganda)

    def test_gets_second_level_location_ie_below_country_if_no_selected_location_given_excluding_the_lowest_level(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        Location.objects.create(name="Kyanja", tree_parent=self.kampala_city, type=village)

        location_widget = LocationWidget(None)
        widget_data = location_widget.get_widget_data()

        self.assertEqual(2, len(widget_data.keys()))
        self.assertNotIn('country', widget_data.keys())
        self.assertNotIn("village", widget_data.keys())
        self.assertIn(self.kampala, widget_data['district'])
        self.assertEqual([], widget_data['city'])

    def test_gets_location_sorted_by_hierarchy_given_a_location_with_parents(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        kyanja = Location.objects.create(name="Kyanja", tree_parent=self.kampala_city, type=village)
        Location.objects.create(name="Kyanja child", tree_parent=kyanja, type=village)

        location_widget = LocationWidget(selected_location=self.kampala_city)
        widget_data = location_widget.get_widget_data()

        self.assertEqual(2, len(widget_data.keys()))
        self.assertIn(self.kampala_city, widget_data['city'])
        self.assertIn(self.kampala, widget_data['district'])
        self.assertNotIn("village", widget_data.keys())
        self.assertNotIn('country', widget_data.keys())

    def test_sorted_by_hierachy_removes_country_types(self):
        slugs = list(LocationType.objects.all().values_list('slug', flat=True))
        old_data = {}
        for slug in slugs:
            old_data[slug] = 'dummy haha' + str(randint)

        location_widget = LocationWidget(selected_location=self.kampala_city)
        new_data = location_widget.sorted_by_hierarchy(old_data)

        self.assertNotIn('country', new_data.keys())
        [self.assertEqual(old_data[key], new_data[key]) for key in new_data.keys()]

    def test_location_widget_truncate_lowest_level_location_type(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        bukoto = Location.objects.create(name='Bukoto', tree_parent=self.kampala_city, type=village)
        some_type = LocationType.objects.create(name='Sometype', slug='sometype')
        LocationTypeDetails.objects.create(location_type=some_type, country=self.uganda)

        location_widget = LocationWidget(selected_location=self.kampala_city)
        widget_data = location_widget.get_widget_data()

        self.assertEqual(3, len(widget_data.keys()))
        self.assertNotIn('country', widget_data.keys())
        self.assertNotIn('sometype', widget_data.keys())
        self.assertIn(self.kampala, widget_data['district'])
        self.assertIn(self.kampala_city, widget_data['city'])
        self.assertIn(bukoto, widget_data['village'])

    def test_location_widget_returns_two_levels_in_the_location_hierarchy_given_two_levels(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        Location.objects.create(name='Bukoto', tree_parent=self.kampala_city, type=village)
        some_type = LocationType.objects.create(name='Sometype', slug='sometype')
        LocationTypeDetails.objects.create(location_type=some_type, country=self.uganda)

        location_widget = LocationWidget(selected_location=self.kampala_city, level=3)
        widget_data = location_widget.get_widget_data()

        self.assertEqual(2, len(widget_data.keys()))
        self.assertNotIn('country', widget_data.keys())
        self.assertNotIn('sometype', widget_data.keys())
        self.assertNotIn('village', widget_data.keys())
        self.assertIn(self.kampala, widget_data['district'])
        self.assertIn(self.kampala_city, widget_data['city'])

    def test_location_widget_knows_next_location_in_hierarchy(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        bukoto = Location.objects.create(name='Bukoto', tree_parent=self.kampala_city, type=village)

        location_widget = LocationWidget(selected_location=self.kampala_city)
        self.assertEqual(village, location_widget.next_type_in_hierarchy())

        location_widget = LocationWidget(selected_location=bukoto)
        self.assertIsNone(location_widget.next_type_in_hierarchy())

    def test_location_widget_appends_ea_data_in_place_of_the_lowest_location_level(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        bukoto = Location.objects.create(name='Bukoto', tree_parent=self.kampala_city, type=village)
        some_type = LocationType.objects.create(name='Sometype', slug='sometype')
        LocationTypeDetails.objects.create(location_type=some_type, country=self.uganda)
        kisasi = Location.objects.create(name='Kisaasi', tree_parent=bukoto, type=some_type)

        ea1 = EnumerationArea.objects.create(name="EA Kisasi1")
        ea2 = EnumerationArea.objects.create(name="EA Kisasi2")
        ea1.locations.add(kisasi)
        ea2.locations.add(kisasi)

        location_widget = LocationWidget(selected_location=bukoto, ea=ea1)
        widget_data = location_widget.get_ea_data()

        self.assertEqual(2, len(widget_data))
        self.assertIn(ea1, widget_data)
        self.assertIn(ea2, widget_data)

    def test_location_widget_appends_empty_ea_data_if_level_is_set(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        bukoto = Location.objects.create(name='Bukoto', tree_parent=self.kampala_city, type=village)
        some_type = LocationType.objects.create(name='Sometype', slug='sometype')
        LocationTypeDetails.objects.create(location_type=some_type, country=self.uganda)
        kisasi = Location.objects.create(name='Kisaasi', tree_parent=bukoto, type=some_type)

        ea1 = EnumerationArea.objects.create(name="EA Kisasi1")
        ea2 = EnumerationArea.objects.create(name="EA Kisasi2")
        ea1.locations.add(kisasi)
        ea2.locations.add(kisasi)

        location_widget = LocationWidget(selected_location=bukoto, ea=ea1, level=3)
        self.failIf(location_widget.get_ea_data())

    def test_location_widget_appends_siblings_ea_if_ea_is_directly_under_parish(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        bukoto = Location.objects.create(name='Bukoto', tree_parent=self.kampala_city, type=village)
        some_type = LocationType.objects.create(name='Sometype', slug='sometype')
        LocationTypeDetails.objects.create(location_type=some_type, country=self.uganda)
        kisasi = Location.objects.create(name='Kisaasi', tree_parent=bukoto, type=some_type)
        kisasi_2 = Location.objects.create(name='Kisaasi 2', tree_parent=bukoto, type=some_type)

        ea1 = EnumerationArea.objects.create(name="EA Kisasi1")
        ea1.locations.add(kisasi)
        ea1.locations.add(kisasi_2)

        location_widget = LocationWidget(selected_location=bukoto, ea=ea1)
        widget_data = location_widget.get_ea_data()

        self.assertEqual(1, len(widget_data))
        self.assertIn(ea1, widget_data)

    def test_location_widget_appends_ea_data_if_selected_location_is_parish_even_if_no_selected_ea(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        bukoto = Location.objects.create(name='Bukoto', tree_parent=self.kampala_city, type=village)
        some_type = LocationType.objects.create(name='Sometype', slug='sometype')
        LocationTypeDetails.objects.create(location_type=some_type, country=self.uganda)
        kisasi = Location.objects.create(name='Kisaasi', tree_parent=bukoto, type=some_type)
        kisasi_2 = Location.objects.create(name='Kisaasi 2', tree_parent=bukoto, type=some_type)
        kisasi_3 = Location.objects.create(name='Kisaasi 2', tree_parent=bukoto, type=some_type)

        ea1 = EnumerationArea.objects.create(name="EA Kisasi1")
        ea2 = EnumerationArea.objects.create(name="EA Kisasi2")
        ea1.locations.add(kisasi)
        ea1.locations.add(kisasi_2)
        ea2.locations.add(kisasi_3)

        location_widget = LocationWidget(selected_location=bukoto)
        widget_data = location_widget.get_ea_data()

        self.assertEqual(2, len(widget_data))
        self.assertIn(ea1, widget_data)
        self.assertIn(ea2, widget_data)

    def test_location_widget_does_not_append_ea_data_of_other_parishes(self):
        village = LocationType.objects.create(name='Village', slug='village')
        LocationTypeDetails.objects.create(location_type=village, country=self.uganda)
        bukoto = Location.objects.create(name='Bukoto', tree_parent=self.kampala_city, type=village)
        some_type = LocationType.objects.create(name='Sometype', slug='sometype')
        LocationTypeDetails.objects.create(location_type=some_type, country=self.uganda)
        kisasi = Location.objects.create(name='Kisaasi', tree_parent=bukoto, type=some_type)
        kisasi_2 = Location.objects.create(name='Kisaasi 2', tree_parent=bukoto, type=some_type)
        kisasi_3 = Location.objects.create(name='Kisaasi 2', tree_parent=bukoto, type=some_type)


        ea1 = EnumerationArea.objects.create(name="EA Kisasi1")
        ea2 = EnumerationArea.objects.create(name="EA Kisasi2")
        ea1.locations.add(kisasi)
        ea1.locations.add(kisasi_2)
        ea2.locations.add(kisasi_3)

        bukoto_2 = Location.objects.create(name='Bukoto 2', tree_parent=self.kampala_city, type=village)
        kisasi_of_bukoto_2 = Location.objects.create(name='Kisaasi', tree_parent=bukoto_2, type=some_type)

        ea3 = EnumerationArea.objects.create(name="EA Kisasi of Bukoto 2")
        ea3.locations.add(kisasi_of_bukoto_2)

        location_widget = LocationWidget(selected_location=bukoto)
        widget_data = location_widget.get_ea_data()

        self.assertEqual(2, len(widget_data))
        self.assertIn(ea1, widget_data)
        self.assertIn(ea2, widget_data)
        self.assertNotIn(ea3, widget_data)

from random import randint
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import LocationTypeDetails
from survey.tests.base_test import BaseTest
from survey.views.location_widget import LocationWidget


class LocationWidgetTest(BaseTest):

    def setUp(self):
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.city = LocationType.objects.create(name='City', slug='city')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.uganda = Location.objects.create(name='Uganda', type=self.country)
        self.country_type_details = LocationTypeDetails.objects.create(location_type=self.country, country=self.uganda)
        self.kampala = Location.objects.create(name='Kampala', tree_parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)

    def test_gets_second_level_location_ie_below_country_if_no_selected_location_given(self):
        location_widget = LocationWidget(None)
        self.assertNotIn('country', location_widget.get_widget_data().keys())
        print location_widget.get_widget_data()
        self.assertIn(self.kampala, location_widget.get_widget_data()['district'])
        self.assertEqual([], location_widget.get_widget_data()['city'])

    def test_gets_location_sorted_by_hierarchy_given_a_location_with_parents(self):
        location_widget = LocationWidget(selected_location=self.kampala_city)
        self.assertIn(self.kampala_city, location_widget.get_widget_data()['city'])
        self.assertIn(self.kampala, location_widget.get_widget_data()['district'])
        self.assertNotIn('country', location_widget.get_widget_data().keys())

    def test_sorted_by_hierachy_removes_country_types(self):
        slugs = LocationType.objects.all().values_list('slug', flat=True)
        print slugs
        old_data = {}
        for slug in slugs:
            old_data[slug] = 'dummy haha' + str(randint)

        location_widget = LocationWidget(selected_location=self.kampala_city)
        new_data = location_widget.sorted_by_hierarchy(old_data)

        self.assertNotIn('country', new_data.keys())
        [self.assertEqual(old_data[key], new_data[key]) for key in new_data.keys()]
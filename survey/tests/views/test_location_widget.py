from rapidsms.contrib.locations.models import Location, LocationType
from survey.tests.base_test import BaseTest
from survey.views.location_widget import LocationWidget


class LocationWidgetTest(BaseTest):

    def setUp(self):
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.city = LocationType.objects.create(name='City', slug='city')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.uganda = Location.objects.create(name='Uganda', type=self.country)
        self.kampala = Location.objects.create(name='Kampala', tree_parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)

    def test_gets_location_with_no_tree_parent_if_no_selected_location(self):
        location_widget = LocationWidget(None)
        self.assertIn(self.uganda, location_widget.get_widget_data()['country'])
        self.assertEqual([], location_widget.get_widget_data()['city'])

    def test_gets_location_sorted_by_hierarchy_given_a_location_with_parents(self):
        location_widget = LocationWidget(selected_location=self.kampala_city)
        self.assertIn(self.kampala_city, location_widget.get_widget_data()['city'])
        self.assertIn(self.kampala, location_widget.get_widget_data()['district'])
        self.assertIn(self.uganda, location_widget.get_widget_data()['country'])
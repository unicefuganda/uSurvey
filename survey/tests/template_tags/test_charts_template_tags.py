from django.test import TestCase
from django.utils.datastructures import SortedDict
from rapidsms.contrib.locations.models import LocationType, Location
from survey.templatetags.chart_template_tags import get_computational_value_by_answer


class ChartTemplateTagsTest(TestCase):
    def setUp(self):
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.region = LocationType.objects.create(name="Region", slug="region")
        self.district = LocationType.objects.create(name="District", slug='district')

        self.uganda = Location.objects.create(name="Uganda", type=self.country)

        self.central = Location.objects.create(name="EAST", type=self.region, tree_parent=self.uganda, )
        self.west = Location.objects.create(name="WEST", type=self.region, tree_parent=self.uganda, )
        self.kampala = Location.objects.create(name="Kampala", tree_parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", tree_parent=self.west, type=self.district)

    def test_formats_title_for_bar_chart_given_formula_and_locations(self):
        hierarchical_data = SortedDict()
        hierarchical_data[self.kampala] = {'OPTION 2': 15.0, 'OPTION 1': 15.0}
        hierarchical_data[self.mbarara] = {'OPTION 2': 40.0, 'OPTION 1': 50.0}
        series = [{'data': [15.0, 40.0], 'name': 'OPTION 2'}, {'data': [15.0, 50.0], 'name': 'OPTION 1'}]
        self.assertEqual(series, get_computational_value_by_answer(hierarchical_data))
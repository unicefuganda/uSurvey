from django.test.testcases import TestCase
from rapidsms.contrib.locations.models import Location
from survey.forms.location_hierarchy import LocationHierarchyForm


class LocationHierarchyFormTest(TestCase):
    def test_knows_the_fields_in_form(self):
        hierarchy_form = LocationHierarchyForm()

        fields = ['country']
        [self.assertIn(field, hierarchy_form.fields) for field in fields]

    def test_should_populate_countries_name(self):
        hierarchy_form = LocationHierarchyForm()

        field = 'country'
        all_countries = Location.objects.filter(type__name='country')
        country_choices = hierarchy_form.fields[field].choices

        [self.assertIn((country_option.id, country_option.name), country_choices) for country_option in all_countries]


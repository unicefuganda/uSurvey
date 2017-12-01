from django.template.defaultfilters import slugify
from django.test import TestCase
from survey.forms.enumeration_area import LocationsFilterForm, get_leaf_locs
from survey.models import EnumerationArea, Location, LocationType


class LocationFormTest(TestCase):
    fixtures = ['enumeration_area', 'locations', 'location_types', ]

    def test_locations_filter_form(self):
        ea = EnumerationArea.objects.last()
        location = ea.locations.first()
        ea_locations = location.get_ancestors(include_self=True)
        data = {location.type.name: location.id for location in ea_locations}
        location_filter = LocationsFilterForm(data=data)
        self.assertNotIn('enumeration_area', location_filter.fields)
        eas = location_filter.get_enumerations()
        # eas basically returns all EAs as per the immediate parent to the smallest unit
        self.assertEquals(eas.count(),
                          EnumerationArea.objects.filter(locations__parent__in=ea_locations).distinct().count())
        self.assertEquals(eas.filter(id=ea.id).count(), 1)
        location_filter = LocationsFilterForm(data=data, include_ea=True)
        self.assertEquals(eas.filter(id=ea.id).count(), 1)
        self.assertIn('enumeration_area', location_filter.fields)
        data['enumeration_area'] = ea.id
        location_filter = LocationsFilterForm(data=data, include_ea=True)
        self.assertTrue(location_filter.is_valid())
        eas = location_filter.get_enumerations()
        self.assertEquals(eas.count(), 1)

    def test_raw_get_leaf_locs_loc_is_int(self):
        ea = EnumerationArea.objects.last()
        location = ea.locations.first()
        locations = get_leaf_locs(loc=location.id)
        self.assertTrue(locations.count(), 1)
        self.assertTrue(locations.last(), location)
        locations = get_leaf_locs(loc=location.parent.id, ea=ea)
        self.assertTrue(locations.count(), 1)
        self.assertTrue(locations.last(), location)
        Location.objects.all().delete()
        locations = get_leaf_locs(loc=location.id)
        self.assertEquals(locations.count(), 0)








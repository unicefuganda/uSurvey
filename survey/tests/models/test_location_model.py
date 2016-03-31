# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models.locations import LocationType, Location
#Eswar commented LocationAutoComplete as model not available
# from survey.models import LocationAutoComplete


class LocationTest(TestCase):
    def test_store(self):
        country = LocationType.objects.create(name="Country", slug='country')
        district = LocationType.objects.create(name="District", parent=country,slug='district')
        county = LocationType.objects.create(name="County", parent=district,slug='county')
        subcounty = LocationType.objects.create(name="SubCounty", parent=county,slug='subcounty')
        parish = LocationType.objects.create(name="Parish", parent=subcounty,slug='parish')
        village = LocationType.objects.create(name="Village", parent=parish,slug='village')


        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, parent=uganda)
        some_county = Location.objects.create(name="County", type=county, parent=kampala)
        some_sub_county = Location.objects.create(name="Subcounty", type=subcounty, parent=some_county)
        some_parish = Location.objects.create(name="Parish", type=parish, parent=some_sub_county)
        some_village = Location.objects.create(name="Village", type=village, parent=some_parish)

        u = Location.objects.get(type__name='Country', name='Uganda')
        report_locations = u.get_descendants(include_self=True).all()
        self.assertEqual(len(report_locations), 6)
        self.assertIn(uganda, report_locations)
        self.assertIn(kampala, report_locations)
        self.assertIn(some_county, report_locations)
        self.assertIn(some_sub_county, report_locations)
        self.assertIn(some_parish, report_locations)
        self.assertIn(some_village, report_locations)
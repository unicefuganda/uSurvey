from django.test import TestCase
from survey.tests.base_test import BaseTest
from survey.models.locations import LocationType, Location


class LocationTest(TestCase):

    def test_fields(self):
        ss_content = Location()
        fields = [str(item.attname) for item in ss_content._meta.fields]
        self.assertEqual(11, len(fields))
        for field in ['id','created','modified','name','type_id','code','parent_id','lft','rght','tree_id','level']:
            self.assertIn(field, fields)

        ss_content = Location()
        fields = [str(item.attname) for item in ss_content._meta.fields]
        self.assertEqual(11, len(fields))
        for field in ['id','created','modified','name','code','lft','rght','tree_id','level','parent_id','type_id']:
            self.assertIn(field, fields)    

    def test_store(self):
        country = LocationType.objects.create(name="Country", slug='country')
        district = LocationType.objects.create(
            name="District", parent=country, slug='district')
        county = LocationType.objects.create(
            name="County", parent=district, slug='county')
        subcounty = LocationType.objects.create(
            name="SubCounty", parent=county, slug='subcounty')
        parish = LocationType.objects.create(
            name="Parish", parent=subcounty, slug='parish')
        village = LocationType.objects.create(
            name="Village", parent=parish, slug='village')

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, parent=uganda)
        some_county = Location.objects.create(
            name="County", type=county, parent=kampala)
        some_sub_county = Location.objects.create(
            name="Subcounty", type=subcounty, parent=some_county)
        some_parish = Location.objects.create(
            name="Parish", type=parish, parent=some_sub_county)
        some_village = Location.objects.create(
            name="Village", type=village, parent=some_parish)

        u = Location.objects.get(type__name='Country', name='Uganda')
        report_locations = u.get_descendants(include_self=True).all()
        self.assertEqual(len(report_locations), 6)
        self.assertIn(uganda, report_locations)
        self.assertIn(kampala, report_locations)
        self.assertIn(some_county, report_locations)
        self.assertIn(some_sub_county, report_locations)
        self.assertIn(some_parish, report_locations)
        self.assertIn(some_village, report_locations)
    def test_unicode_text(self):
        l = Location.objects.create(name="module name")
        self.assertEqual(l.name, str(l))
class LocationTest(TestCase):
    def test_unicode_text(self):
        lt = LocationType.objects.create(name="module name")
        self.assertEqual(lt.name, str(lt))
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models.locations import Location, LocationType
from survey.models import Survey, LocationTypeDetails

from survey.models.batch import Batch
from survey.models.enumeration_area import EnumerationArea
from survey.tests.base_test import BaseTest


class EATest(BaseTest):
    def setUp(self):
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1, survey=self.survey)
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.region = LocationType.objects.create(name="Region", slug="region")
        self.district = LocationType.objects.create(name="District", slug='district')

        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        LocationTypeDetails.objects.create(location_type=self.country, country=self.uganda)
        self.west = Location.objects.create(name="WEST", type=self.region, tree_parent=self.uganda)
        self.central = Location.objects.create(name="CENTRAL", type=self.region, tree_parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", tree_parent=self.central, type=self.district)
        self.wakiso = Location.objects.create(name="Wakiso", tree_parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", tree_parent=self.west, type=self.district)

    def test_ea_fields(self):
        ea = EnumerationArea()

        fields = [str(item.attname) for item in ea._meta.fields]
        for field in ['id', 'name', 'created', 'modified', 'code']:
            self.assertIn(field, fields)
        self.assertEqual(len(fields), 5)

    def test_store(self):
        ea = EnumerationArea.objects.create(name="EA1")
        self.failUnless(ea.id)

    def test_add_location(self):
        self.location_type_country = LocationType.objects.create(name="Country1", slug='country1')
        self.location_type_district = LocationType.objects.create(name="District2", parent=self.location_type_country,slug='district2')
        self.location_type_district1 = LocationType.objects.create(name="District1", parent=self.location_type_country,slug='district1')
        self.location = Location.objects.create(name="Kangala", type=self.location_type_country, code=256)
        self.locations_district=Location.objects.create(name="dist",type=self.district,code=234)
        self.locations_district1=Location.objects.create(name="dist1",type=self.district,code=234)
        ea = EnumerationArea.objects.create(name="EA1")
        ea.locations.add(self.locations_district)
        self.failUnless(EnumerationArea.objects.filter(locations=8))

        ea.locations.add(self.locations_district1)
        self.assertEqual(2, ea.locations.all().count())
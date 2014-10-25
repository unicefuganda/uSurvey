import os
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import LocationTypeDetails
from survey.management.commands.import_location import Command
from survey.tests.base_test import BaseTest
from mock import patch

class FakeStdout(object):
    def write(self, msg):
        return "haha %s"%msg

class FakeCommand(Command):
    def __init__(self):
        super(FakeCommand, self).__init__()
        self.stdout = FakeStdout()


class ImportLocationTest(BaseTest):
    def setUp(self):
        self.data = [['RegionName', 'DistrictName', 'CountyName'],
                     ['region1', 'district1', 'county1'],
                     ['region2', 'district2', 'county2']]

        self.write_to_csv('wb', self.data)
        self.filename = 'test.csv'
        file = open(self.filename, 'rb')
        self.importer = FakeCommand()
        self.region = LocationType.objects.create(name='Region', slug='region')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.county = LocationType.objects.create(name='County', slug='county')
        LocationTypeDetails.objects.create(location_type=self.region, required=True, has_code=False)
        LocationTypeDetails.objects.create(location_type=self.district, required=True, has_code=False)
        LocationTypeDetails.objects.create(location_type=self.county, required=True, has_code=False)

    def tearDown(self):
        os.system("rm -rf %s"%self.filename)

    def test_should_not_recreate_types_and_locations(self):
        self.importer.handle(self.filename)
        types = [type_name.replace('Name', '') for type_name in self.data[0]]
        for type in types:
            self.assertEqual(1, LocationType.objects.filter(name=type).count())

    def test_should_create_locations(self):
        self.importer.handle(self.filename)
        types = [type_name.replace('Name', '') for type_name in self.data[0]]
        for locations in self.data[1:]:
            [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for
             index, location_name in enumerate(locations)]

    def test_should_respect_locations_hierarchy(self):
        self.importer.handle(self.filename)
        for locations in self.data[1:]:
            for index, location_name in enumerate(locations[:-2]):
                tree_parent = Location.objects.get(name=location_name)
                self.assertEqual(tree_parent, Location.objects.get(name=locations[index+1]).tree_parent)

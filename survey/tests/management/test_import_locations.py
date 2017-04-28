import os
from survey.models.locations import *
from survey.management.commands.import_location import Command
from survey.tests.base_test import BaseTest
from survey.management.commands import *


class FakeStdout(object):

    def write(self, msg):
        return "haha %s" % msg


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
        open(self.filename, 'rb')
        self.importer = FakeCommand()
        self.region = LocationType.objects.create(
            name='Region1', slug='region')
        self.district = LocationType.objects.create(
            name='District1', slug='district', parent=self.region)
        self.county = LocationType.objects.create(
            name='County1', slug='county', parent=self.district)

    def tearDown(self):
        os.system("rm -rf %s" % self.filename)

    def test_should_not_recreate_types_and_locations(self):
        self.importer.handle(self.filename)
        types = [type_name.replace('Name', '') for type_name in self.data[0]]
        for type in types:
            self.assertEqual(1, LocationType.objects.filter(name=type).count())

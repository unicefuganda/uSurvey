import os
from survey.models.locations import *
from survey.models import LocationTypeDetails
from survey.management.commands.import_countries import Command
from survey.tests.base_test import BaseTest


class FakeStdout(object):

    def write(self, msg):
        return "haha %s" % msg


class FakeCommand(Command):

    def __init__(self):
        super(FakeCommand, self).__init__()
        self.stdout = FakeStdout()


class ImportCountriesTest(BaseTest):

    def setUp(self):
        self.data = [['uganda'], ['ayoyo'], ['hoho']]

        self.write_to_csv('wb', self.data)
        self.filename = 'test.csv'
        open(self.filename, 'rb')
        self.importer = FakeCommand()
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        LocationTypeDetails.objects.create(
            location_type=self.country, required=True, has_code=False)

    def tearDown(self):
        os.system("rm -rf %s" % self.filename)

    def test_should_create_country_type_if_not_existing_and_not_recreate_country_types_if_exists(self):
        self.importer.handle(self.filename)
        self.assertEqual(1, LocationType.objects.filter(
            name="Country").count())
        self.country.delete()
        self.importer.handle(self.filename)
        self.failUnless(LocationType.objects.filter(name="Country"))

    def test_should_create_countries_without_tree_parent(self):
        self.importer.handle(self.filename)
        for country_name in self.data:
            self.failUnless(Location.objects.filter(name=country_name[
                            0], type__name__iexact="country", parent=None))

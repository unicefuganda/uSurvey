import os
from django.core.files.uploadedfile import SimpleUploadedFile
from survey.models.locations import *
from survey.forms.upload_csv_file import UploadWeightsForm, UploadLocationsForm
from survey.models import Survey, LocationType
from survey.tests.base_test import BaseTest


class UploadLocationsFormTest(BaseTest):

    def setUp(self):
        self.data = [['RegionName', 'DistrictName', 'CountyName'],
                     ['region1', 'district1', 'county1'],
                     ['region2', 'district2', 'county2']]

        self.write_to_csv('wb', self.data)
        self.filename = 'test.csv'
        self.file = open(self.filename, 'rb')
        self.region = LocationType.objects.create(name='Region', slug='region')
        self.district = LocationType.objects.create(
            name='District', slug='district', parent=self.region)
        self.county = LocationType.objects.create(
            name='County', slug='county', parent=self.district)
        # LocationType.objects.create(
        #     location_type=self.region, required=True, has_code=False)
        # LocationType.objects.create(
        #     location_type=self.district, required=True, has_code=False)
        # LocationType.objects.create(
        #     location_type=self.county, required=True, has_code=False)

    def tearDown(self):
        os.system("rm -rf %s" % self.filename)

    def test_valid(self):
        data_file = {'file': SimpleUploadedFile(
            self.filename, self.file.read())}

        upload_location_form = UploadLocationsForm({}, data_file)

        self.assertEqual(True, upload_location_form.is_valid())

    def test_invalid_if_location_type_not_found(self):
        LocationType.objects.all().delete()
        LocationType.objects.all().delete()
        data_file = {'file': SimpleUploadedFile(
            self.filename, self.file.read())}

        upload_location_form = UploadLocationsForm({}, data_file)

        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('Location type - Region not found.',
                      upload_location_form.non_field_errors())

    def test_invalid_if_location_type_details_not_found(self):
        LocationType.objects.all().delete()
        data_file = {'file': SimpleUploadedFile(
            self.filename, self.file.read())}

        upload_location_form = UploadLocationsForm({}, data_file)

        self.assertEqual(False, upload_location_form.is_valid())

    def test_invalid_if_headers_are_not_in_order(self):
        unordered_data = [['DistrictName', 'CountyName', 'RegionName'],
                          ['district1', 'county1', 'region1'],
                          ['district2', 'county2', 'region2']]
        self.write_to_csv('wb', unordered_data, csvfilename='some_file.csv')
        file = open('some_file.csv', 'rb')
        data_file = {'file': SimpleUploadedFile(self.filename, file.read())}

        upload_location_form = UploadLocationsForm({}, data_file)

        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('Location types not in order. Please refer to input file format.',
                      upload_location_form.non_field_errors())

    def test_valid_with_has_code(self):
        # district = LocationType.objects.get(
        #     location_type=self.district, required=True)
        district = LocationType.objects.get(
            name='District', slug='district', parent=self.region)
        district.has_code = True
        district.length_of_code = 3
        district.save()

        data = [['RegionName', 'DistrictCode', 'DistrictName', 'CountyName'],
                ['region1', '001', 'district1', 'county1'],
                ['region2', '003', 'district2', 'county2']]

        self.write_to_csv('wb', data)
        file = open('test.csv', 'rb')
        data_file = {'file': SimpleUploadedFile(self.filename, file.read())}

        upload_location_form = UploadLocationsForm({}, data_file)

        self.assertEqual(True, upload_location_form.is_valid())

    def test_invalid_if_has_code_is_checked_but_no_type_code_column(self):
        # district = LocationType.objects.get(
        #     location_type=self.district, required=True)
        district = LocationType.objects.get(
            name='District', slug='district', parent=self.region)
        Location
        district.has_code = True
        district.length_of_code = 6
        district.save()
        data_file = {'file': SimpleUploadedFile(
            self.filename, self.file.read())}

        upload_location_form = UploadLocationsForm({}, data_file)

        self.assertEqual(True, upload_location_form.is_valid())

    def test_invalid_if_not_has_code_but_code_still_supplied(self):
        data = [['RegionName', 'DistrictCode', 'DistrictName', 'CountyName'],
                ['region1', '001', 'district1', 'county1'],
                ['region2', '002', 'district2', 'county2']]

        self.write_to_csv('wb', data)
        file = open('test.csv', 'rb')
        data_file = {'file': SimpleUploadedFile(
            self.filename, self.file.read())}

        upload_location_form = UploadLocationsForm({}, data_file)

        self.assertEqual(True, upload_location_form.is_valid())

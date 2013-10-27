import os
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import LocationTypeDetails
from survey.services.location_upload import UploadLocation
from survey.tests.base_test import BaseTest


class LocationUploadHelper(BaseTest):
    def setUp(self):
        self.data = [['RegionName', 'DistrictName', 'CountyName'],
                     ['region1', 'district1', 'county1'],
                     ['region2', 'district2', 'county2']]

        self.write_to_csv('wb', self.data)
        self.filename = 'test.csv'
        file = open(self.filename, 'rb')
        self.uploader = UploadLocation(file)
        self.region = LocationType.objects.create(name='Region', slug='region')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.county = LocationType.objects.create(name='County', slug='county')
        LocationTypeDetails.objects.create(location_type=self.region, required=True, has_code=False)
        LocationTypeDetails.objects.create(location_type=self.district, required=True, has_code=False)
        LocationTypeDetails.objects.create(location_type=self.county, required=True, has_code=False)

    def tearDown(self):
        os.system("rm -rf %s"%self.filename)


    def test_should_return_false__and_message_if_location_type_not_found(self):
        LocationType.objects.all().delete()
        LocationTypeDetails.objects.all().delete()
        status, message = self.uploader.upload()
        self.assertFalse(status)
        self.assertEqual(message, 'Locations not uploaded. Location type - Region not found.')

    def test_should_return_false__and_message_if_location_type_details_not_found(self):
        LocationTypeDetails.objects.all().delete()
        status, message = self.uploader.upload()
        self.assertFalse(status)
        self.assertEqual(message, 'Locations not uploaded. Location type details for Region not found.')

    def test_should_return_true_if_location_type_exists(self):
        status, message = self.uploader.upload()
        self.assertTrue(status)
        types = [type_name.replace('Name', '') for type_name in self.data[0]]
        for locations in self.data[1:]:
            [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for
             index, location_name in enumerate(locations)]
        self.assertEqual(message, 'Locations successfully uploaded.')

    def test_should_return_false_if_required_location_type_is_blank(self):
        missing_fields_data = [['region3', '', 'county3']]
        self.write_to_csv('ab', missing_fields_data)
        file = open('test.csv', 'rb')
        self.uploader = UploadLocation(file)
        status, message = self.uploader.upload()
        self.assertFalse(status)
        self.assertEqual("Locations not uploaded. Missing data: DistrictName on row 3 should not be empty.", message)

    def test_should_return_false_and_error_message_if_headers_are_not_in_order(self):
        unordered_data = [['DistrictName', 'CountyName', 'RegionName'],
                          ['district1', 'county1', 'region1'],
                          ['district2', 'county2', 'region2']]
        self.write_to_csv('wb', unordered_data, csvfilename='some_file.csv')
        file = open('some_file.csv', 'rb')
        uploader = UploadLocation(file)
        status, message = uploader.upload()
        self.assertFalse(status)
        self.assertEqual(message, 'Locations not uploaded. Location types not in order. Please refer to input file format.')

    def test_regroup_with_code(self):
        a = [1, 2, 3, 4, 5, 6, 7, 8]
        self.assertEqual([[1, 2], [3, 4], [5, 6], [7, 8]], self.uploader.regroup_with_code(a, [2, 2, 2, 2]))
        self.assertEqual([[1], [2, 3, 4], [5, 6], [7], [8]], self.uploader.regroup_with_code(a, [1, 3, 2, 1, 1]))

    def test_remove_trailing_name_in_headers(self):
        headers = ['heheName', 'somethingCode', 'hahaName', 'blablaCode', 'hihihi', 'hohoho']
        self.assertEqual(['hehe', 'haha', 'hihihi', 'hohoho'], self.uploader.remove_trailing('Name', in_array=headers, exclude='Code'))

    def test_has_code_success(self):
        district = LocationTypeDetails.objects.get(location_type=self.district, required=True)
        district.has_code = True
        district.length_of_code = 3
        district.save()

        data = [['RegionName', 'DistrictCode', 'DistrictName', 'CountyName'],
                     ['region1', '001', 'district1', 'county1'],
                     ['region2', '003','district2', 'county2']]

        self.write_to_csv('wb', data)
        file = open('test.csv', 'rb')
        uploader = UploadLocation(file)

        status, message = uploader.upload()
        self.assertTrue(status)
        types = uploader.remove_trailing('Name', data[0], exclude='Code')
        data_locations = data[1:]
        [locations.pop(1) for locations in data_locations]
        print data_locations
        for locations in data_locations:
            [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for
             index, location_name in enumerate(locations)]

        self.assertEqual('Locations successfully uploaded.', message)

    def test_should_return_false_and_error_message_if_has_code_is_checked_but_no_type_code_column(self):
        district = LocationTypeDetails.objects.get(location_type=self.district, required=True)
        district.has_code = True
        district.length_of_code = 6
        district.save()
        status, message = self.uploader.upload()
        self.assertFalse(status)
        self.assertEqual(message, 'Locations not uploaded. DistrictCode column should be before DistrictName column. Please refer to input file format.')

    def test_should_return_false_and_error_message_if_length_of_code_is_not_matched(self):
        district = LocationTypeDetails.objects.get(location_type=self.district, required=True)
        district.has_code = True
        district.length_of_code = 3
        district.save()

        some_code_with_length_less_than_3 = '02'
        data = [['RegionName', 'DistrictCode', 'DistrictName', 'CountyName'],
                     ['region1', '001', 'district1', 'county1'],
                     ['region2', some_code_with_length_less_than_3,'district2', 'county2']]

        self.write_to_csv('wb', data)
        file = open('test.csv', 'rb')
        uploader = UploadLocation(file)

        status, message = uploader.upload()
        self.assertFalse(status)
        self.assertEqual('Locations not uploaded. DistrictCode on row 2 is shorter than the required 3 digits.', message)

    def test_should_return_false_and_error_message_if_not_has_code_but_code_still_supplied(self):
        data = [['RegionName', 'DistrictCode', 'DistrictName', 'CountyName'],
                     ['region1', '001', 'district1', 'county1'],
                     ['region2', '002','district2', 'county2']]

        self.write_to_csv('wb', data)
        file = open('test.csv', 'rb')
        uploader = UploadLocation(file)

        status, message = uploader.upload()
        self.assertFalse(status)
        self.assertEqual('Locations not uploaded. District has no code. The column DistrictCode should be removed. Please refer to input file format.', message)

    def test_has_code_success_with_special_characters_in_csv_file(self):
        district = LocationTypeDetails.objects.get(location_type=self.district, required=True)
        district.has_code = True
        district.length_of_code = 3
        district.save()

        data = [['RegionName', 'DistrictCode', 'DistrictName', 'CountyName'],
                     ['region1', '001', 'district1%$#!_*', 'county1'],
                     ['region2', '003','district2', 'county2']]

        self.write_to_csv('wb', data)
        file = open('test.csv', 'rb')
        uploader = UploadLocation(file)

        status, message = uploader.upload()
        self.assertTrue(status)
        types = uploader.remove_trailing('Name', data[0], exclude='Code')
        data_locations = data[1:]
        [locations.pop(1) for locations in data_locations]
        for locations in data_locations:
            [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for
             index, location_name in enumerate(locations)]

        self.assertEqual('Locations successfully uploaded.', message)

    def test_has_code_success_with_suffix_Name_omitted_in_headers(self):
        district = LocationTypeDetails.objects.get(location_type=self.district, required=True)
        district.has_code = True
        district.length_of_code = 3
        district.save()

        data = [['Region', 'DistrictCode', 'District', 'CountyName'],
                     ['region1', '001', 'district1', 'county1'],
                     ['region2', '003','district2', 'county2']]

        self.write_to_csv('wb', data)
        file = open('test.csv', 'rb')
        uploader = UploadLocation(file)

        status, message = uploader.upload()
        self.assertTrue(status)
        types = uploader.remove_trailing('Name', data[0], exclude='Code')
        data_locations = data[1:]
        [locations.pop(1) for locations in data_locations]
        for locations in data_locations:
            [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for
             index, location_name in enumerate(locations)]

        self.assertEqual('Locations successfully uploaded.', message)

    def test_not_csv_file(self):
        self.filename = 'not_csv.xls'
        self.generate_non_csv_file(self.filename)
        file = open(self.filename,'rb')
        uploader = UploadLocation(file)
        status, message = uploader.upload()
        self.assertFalse(status)
        self.assertEqual('Locations not uploaded. not_csv.xls is not a csv file.', message)
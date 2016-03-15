# import os
# from rapidsms.contrib.locations.models import LocationType, Location
# from survey.models.locations import *
# from survey.models import LocationTypeDetails, UploadErrorLog
# from survey.services.location_upload import UploadLocation
# from survey.tests.base_test import BaseTest
#
#
# class LocationUploadHelper(BaseTest):
#     def setUp(self):
#         self.data = [['RegionName', 'DistrictName', 'CountyName'],
#                      ['region1', 'district1', 'county1'],
#                      ['region2', 'district2', 'county2']]
#
#         self.write_to_csv('wb', self.data)
#         self.filename = 'test.csv'
#         file = open(self.filename, 'rb')
#         self.uploader = UploadLocation(file)
#         self.region = LocationType.objects.create(name='Region', slug='region')
#         self.district = LocationType.objects.create(name='District', slug='district', parent=self.region)
#         self.county = LocationType.objects.create(name='County', slug='county', parent=self.district)
#         LocationTypeDetails.objects.create(location_type=self.region, required=True, has_code=False)
#         LocationTypeDetails.objects.create(location_type=self.district, required=True, has_code=False)
#         LocationTypeDetails.objects.create(location_type=self.county, required=True, has_code=False)
#
#     def tearDown(self):
#         os.system("rm -rf %s"%self.filename)
#
#     # def test_should_create_locations(self):
#     #     self.uploader.upload()
#     #     types = [type_name.replace('Name', '') for type_name in self.data[0]]
#     #     for locations in self.data[1:]:
#     #         [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for
#     #          index, location_name in enumerate(locations)]
#
#     def test_should_log_error_if_a_required_location_type_is_left_blank(self):
#         missing_fields_data = [['region3', '', 'county3']]
#         self.write_to_csv('ab', missing_fields_data)
#         file = open('test.csv', 'rb')
#         self.uploader = UploadLocation(file)
#         self.uploader.upload()
#         error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
#         self.assertEqual(1, error_log.count())
#         self.failUnless(error_log.filter(row_number=4,
#                                          error='Missing data: DistrictName should not be empty.'))
#     #
#     # def test_regroup_with_code(self):
#     #     a = [1, 2, 3, 4, 5, 6, 7, 8]
#     #     self.assertEqual([[1, 2], [3, 4], [5, 6], [7, 8]], self.uploader.regroup_with_code(a, [2, 2, 2, 2]))
#     #     self.assertEqual([[1], [2, 3, 4], [5, 6], [7], [8]], self.uploader.regroup_with_code(a, [1, 3, 2, 1, 1]))
#     #
#     # def test_create_code(self):
#     #     district = LocationTypeDetails.objects.get(location_type=self.district, required=True)
#     #     district.has_code = True
#     #     district.length_of_code = 3
#     #     district.save()
#     #
#     #     data = [['RegionName', 'DistrictCode', 'DistrictName', 'CountyName'],
#     #                  ['region1', '001', 'district1', 'county1'],
#     #                  ['region2', '003','district2', 'county2']]
#     #
#     #     self.write_to_csv('wb', data)
#     #     file = open('test.csv', 'rb')
#     #     uploader = UploadLocation(file)
#     #
#     #     uploader.upload()
#     #     types = uploader.remove_trailing('Name', data[0], exclude='Code')
#     #     data_locations = data[1:]
#     #     codes = [locations.pop(1) for locations in data_locations]
#     #     for locations in data_locations:
#     #         [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for
#     #          index, location_name in enumerate(locations)]
#     #
#     #     [self.failUnless(LocationCode.objects.filter(code=code)) for code in codes]
#     #
#     #
#     # def test_should_log_error_if_length_of_code_is_not_matched(self):
#     #     district = LocationTypeDetails.objects.get(location_type=self.district, required=True)
#     #     district.has_code = True
#     #     district.length_of_code = 3
#     #     district.save()
#     #
#     #     some_code_with_length_less_than_3 = '02'
#     #     data = [['RegionName', 'DistrictCode', 'DistrictName', 'CountyName'],
#     #                  ['region1', '001', 'district1', 'county1'],
#     #                  ['region2', some_code_with_length_less_than_3,'district2', 'county2']]
#     #
#     #     self.write_to_csv('wb', data)
#     #     file = open('test.csv', 'rb')
#     #     uploader = UploadLocation(file)
#     #
#     #     uploader.upload()
#     #     error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
#     #     self.assertEqual(1, error_log.count())
#     #     self.failUnless(error_log.filter(row_number=3,
#     #                                      error='DistrictCode is shorter or longer than the required 3 digits.'))
#     #
#     # def test_create_location_and_code_with_special_characters_in_csv_file(self):
#     #     district = LocationTypeDetails.objects.get(location_type=self.district, required=True)
#     #     district.has_code = True
#     #     district.length_of_code = 3
#     #     district.save()
#     #
#     #     data = [['RegionName', 'DistrictCode', 'DistrictName', 'CountyName'],
#     #                  ['region1', '001', 'district1%$#!_*', 'county1'],
#     #                  ['region2', '003','district2', 'county2']]
#     #
#     #     self.write_to_csv('wb', data)
#     #     file = open('test.csv', 'rb')
#     #     uploader = UploadLocation(file)
#     #
#     #     uploader.upload()
#     #     types = uploader.remove_trailing('Name', data[0], exclude='Code')
#     #     data_locations = data[1:]
#     #     codes = [locations.pop(1) for locations in data_locations]
#     #     for locations in data_locations:
#     #         [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for
#     #          index, location_name in enumerate(locations)]
#     #
#     #     [self.failUnless(LocationCode.objects.filter(code=code)) for code in codes]
#     #
#     # def test_create_location_and_code_when_suffix_Name_omitted_in_headers(self):
#     #     district = LocationTypeDetails.objects.get(location_type=self.district, required=True)
#     #     district.has_code = True
#     #     district.length_of_code = 3
#     #     district.save()
#     #
#     #     data = [['Region', 'DistrictCode', 'District', 'CountyName'],
#     #                  ['region1', '001', 'district1', 'county1'],
#     #                  ['region2', '003','district2', 'county2']]
#     #
#     #     self.write_to_csv('wb', data)
#     #     file = open('test.csv', 'rb')
#     #     uploader = UploadLocation(file)
#     #
#     #     uploader.upload()
#     #     types = uploader.remove_trailing('Name', data[0], exclude='Code')
#     #     data_locations = data[1:]
#     #     codes = [locations.pop(1) for locations in data_locations]
#     #     for locations in data_locations:
#     #         [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for
#     #          index, location_name in enumerate(locations)]
#     #
#     #     [self.failUnless(LocationCode.objects.filter(code=code)) for code in codes]
#     #
#     # def test_not_csv_file(self):
#     #     Location.objects.all().delete()
#     #     LocationCode.objects.all().delete()
#     #     self.filename = 'not_csv.xls'
#     #     self.generate_non_csv_file(self.filename)
#     #     file = open(self.filename,'rb')
#     #     uploader = UploadLocation(file)
#     #
#     #     uploader.upload()
#     #     error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
#     #     self.failUnless(error_log.filter(error='Locations not uploaded. %s is not a valid csv file.' % self.filename))
#     #     self.failIf(Location.objects.all())
#     #     self.failIf(LocationCode.objects.all())

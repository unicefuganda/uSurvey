from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType
from survey.models import LocationTypeDetails
from survey.tests.base_test import BaseTest
from survey.views.location_upload_view_helper import UploadLocation
import csv


class LocationUploadHelper(BaseTest):
    def setUp(self):
        data = [['Region', 'District','County'],
                ['region1', 'district1','county1'],
                ['region2','district2','county2']]

        self.write_to_csv('wb',data)
        file = open('test.csv', 'rb')
        self.uploader = UploadLocation(file)
        self.region = LocationType.objects.create(name='Region',slug='region')
        self.district = LocationType.objects.create(name='District',slug='district')
        self.county = LocationType.objects.create(name='County',slug='county')
        LocationTypeDetails.objects.create(location_type=self.region, required=True, has_code=False)
        LocationTypeDetails.objects.create(location_type=self.district, required=True, has_code=False)
        LocationTypeDetails.objects.create(location_type=self.county, required=True, has_code=False)

    def test_should_return_false__and_message_if_location_type_not_found(self):
        LocationType.objects.all().delete()
        LocationTypeDetails.objects.all().delete()
        status,message= self.uploader.upload()
        self.assertFalse(status)
        self.assertEqual(message, 'Location type - Region not created')

    def test_should_return_true_if_location_type_exists(self):
        status,message= self.uploader.upload()
        self.assertTrue(status)
        self.assertEqual(message, 'Successfully uploaded')

    def test_should_return_false_if_required_location_type_is_blank(self):
        missing_fields_data=[['region3','','county3']]
        self.write_to_csv('ab', missing_fields_data)
        file = open('test.csv', 'rb')
        self.uploader = UploadLocation(file)
        status,message= self.uploader.upload()
        self.assertFalse(status)
        self.assertEqual(message, 'Missing data')

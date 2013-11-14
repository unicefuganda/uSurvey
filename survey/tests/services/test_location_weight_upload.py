import os
from rapidsms.contrib.locations.models import Location
from survey.models import Survey
from survey.services.location_weights_upload import UploadLocationWeights
from survey.tests.base_test import BaseTest


class LocationWeightUploadHelper(BaseTest):
    def setUp(self):
        self.data = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                     ['region1', 'district1', 'county1', '0.01'],
                     ['region2', 'district2', 'county2', '0.1']]

        self.write_to_csv('wb', self.data)
        self.filename = 'test.csv'
        _file = open(self.filename, 'rb')
        self.uploader = UploadLocationWeights(_file)
        self.survey = Survey.objects.create(name="Survey A")

    def tearDown(self):
        os.system("rm -rf %s" % self.filename)

    def test_should_return_false__and_message_if_location_not_found(self):
        Location.objects.all().delete()
        status, message = self.uploader.upload(self.survey)
        self.assertFalse(status)
        self.assertEqual(message, 'Location weights not uploaded. There is no county with name: county1, in district1.')

    def test_should_return_false__and_message_if_location_is_blank(self):
        data = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                ['region1', 'district1', '', '0.2']]
        self.write_to_csv('wb', data)
        _file = open(self.filename, 'rb')

        region = Location.objects.create(name="region1")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)

        uploader = UploadLocationWeights(_file)
        status, message = uploader.upload(self.survey)
        self.assertFalse(status)
        self.assertEqual(message, 'Location weights not uploaded. '
                                  'There is no county with name: , in district1.')

    def test_should_return_false__and_message_if_location_tree_parent_does_not_match_one_provided(self):
        region = Location.objects.create(name="region name not matching the one in first row of file")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)
        status, message = self.uploader.upload(self.survey)
        self.assertFalse(status)
        self.assertEqual(message, 'Location weights not uploaded. '
                                  'The location hierarchy region1 >> district1 >> county1 does not exist.')

    def test_should_return_false__and_message_if_no_weight_is_provided(self):
        data = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                ['region1', 'district1', 'county1', '']]
        self.write_to_csv('wb', data)
        _file = open(self.filename, 'rb')

        region = Location.objects.create(name="region1")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)

        uploader = UploadLocationWeights(_file)

        status, message = uploader.upload(self.survey)
        self.assertFalse(status)
        self.assertEqual(message, 'Location weights not uploaded. Selection probability must be a number.')

    def test_should_return_false__and_message_if_weight_is_NaN(self):
        data = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                ['region1', 'district1', 'county1', 'bla bli blo not a number']]
        self.write_to_csv('wb', data)
        _file = open(self.filename, 'rb')

        region = Location.objects.create(name="region1")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)

        uploader = UploadLocationWeights(_file)

        status, message = uploader.upload(self.survey)
        self.assertFalse(status)
        self.assertEqual(message, 'Location weights not uploaded. Selection probability must be a number.')

    def test_should_return_true__and_success_message_if_valid_csv_provided(self):
        data = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                ['region1', 'district1', 'county1', '0.02']]
        self.write_to_csv('wb', data)
        _file = open(self.filename, 'rb')

        region = Location.objects.create(name="region1")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)

        region = Location.objects.create(name="region2")
        district = Location.objects.create(name="district2", tree_parent=region)
        Location.objects.create(name="county2", tree_parent=district)

        uploader = UploadLocationWeights(_file)

        status, message = uploader.upload(self.survey)
        self.assertTrue(status)
        self.assertEqual(message, 'Location weights successfully uploaded.')
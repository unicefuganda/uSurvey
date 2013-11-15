import os
from datetime import datetime, timedelta
from rapidsms.contrib.locations.models import Location
from survey.models import Survey, UploadErrorLog, LocationWeight
from survey.services.location_weights_upload import UploadLocationWeights
from survey.tests.base_test import BaseTest
from django.utils.timezone import utc


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
        self.uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.assertEqual(2, error_log.count())
        self.failUnless(error_log.filter(row_number=1,
                                         error='There is no county with name: county1, in district1.'))
        self.failUnless(error_log.filter(row_number=2,
                                         error='There is no county with name: county2, in district2.'))

    def test_should_return_false__and_message_if_location_is_blank(self):
        data = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                ['region1', 'district1', '', '0.2']]
        self.write_to_csv('wb', data)
        _file = open(self.filename, 'rb')

        region = Location.objects.create(name="region1")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)

        uploader = UploadLocationWeights(_file)
        uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.assertEqual(1, error_log.count())
        self.failUnless(error_log.filter(row_number=1,
                                         error='There is no county with name: , in district1.'))

    def test_should_return_false__and_message_if_location_tree_parent_does_not_match_one_provided(self):
        region = Location.objects.create(name="region name not matching the one in first row of file")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)
        self.uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.assertEqual(2, error_log.count())
        self.failUnless(error_log.filter(row_number=1,
                                         error='The location hierarchy region1 >> district1 >> county1 does not exist.'))

    def test_should_return_false__and_message_if_no_weight_is_provided(self):
        data = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                ['region1', 'district1', 'county1', '']]
        self.write_to_csv('wb', data)
        _file = open(self.filename, 'rb')

        region = Location.objects.create(name="region1")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)

        uploader = UploadLocationWeights(_file)

        uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.assertEqual(1, error_log.count())
        self.failUnless(error_log.filter(row_number=1,
                                         error='Selection probability must be a number.'))

    def test_should_return_false__and_message_if_weight_is_NaN(self):
        data = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                ['region1', 'district1', 'county1', 'bla bli blo not a number']]
        self.write_to_csv('wb', data)
        _file = open(self.filename, 'rb')

        region = Location.objects.create(name="region1")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)

        uploader = UploadLocationWeights(_file)

        uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.assertEqual(1, error_log.count())
        self.failUnless(error_log.filter(row_number=1,
                                         error='Selection probability must be a number.'))

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

        uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.failIf(error_log.filter(row_number=1, error='Selection probability must be a number.'))

        self.failUnless(LocationWeight.objects.filter(location__name=data[1][2], selection_probability=data[1][3]))

    def test_deletes_one_month_old_error_logs_every_time_an_instance_is_created(self):
        UploadErrorLog.objects.all().delete()
        error_location = UploadErrorLog.objects.create(model='LOCATION', filename=self.filename, error="Some errors location")
        error_now = UploadErrorLog.objects.create(model=self.uploader.MODEL, filename=self.filename, error="Some errors now")
        two_months_old_error_log = UploadErrorLog.objects.create(model=self.uploader.MODEL, filename=self.filename, error="Some different errors")
        two_months_old_error_log.created = datetime.utcnow().replace(tzinfo=utc) - timedelta(days=31)
        two_months_old_error_log.save()

        UploadLocationWeights(open(self.filename, 'rb'))

        two_months_old_error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename, error="Some different errors")
        self.failIf(two_months_old_error_log)

        error_location = UploadErrorLog.objects.filter(model='LOCATION', filename=self.filename, error="Some errors location")
        self.failUnless(error_location)
        error_now = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename, error="Some errors now")
        self.failUnless(error_now)

    def test_not_csv_file(self):
        self.filename = 'not_csv.xls'
        self.generate_non_csv_file(self.filename)
        file = open(self.filename,'rb')
        uploader = UploadLocationWeights(file)

        uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.failUnless(error_log.filter(error='Location weights not uploaded. %s is not a csv file.' % self.filename))
import os
from datetime import datetime, timedelta
from django.core.files import File
from survey.services.csv_uploader import CSVUploader, UploadService
from survey.tests.base_test import BaseTest
from survey.models import UploadErrorLog
from django.utils.timezone import utc

class CSVUploaderTest(BaseTest):

    def setUp(self):
        self.filename = 'simple.csv'
        self.data = [["0", "1", "2"], ["0", "1", "2"], ["0", "1", "2"]]
        self.headers = ["Region", "District", "County"]

    def tearDown(self):
        os.system("rm -rf %s" % self.filename)

    def generate_csv_file(self, filename):
        data = [self.headers]
        data.extend(self.data)
        self.write_to_csv('wb', data, filename)

    def test_read_headers_and_data(self):
        self.generate_csv_file(self.filename)
        file = File(open(self.filename, 'rb'))
        headers, data = CSVUploader(file).split_content()
        self.assertEqual(self.headers, headers)
        self.assertEqual(self.data, data)

class UploaderServiceTest(BaseTest):

    def setUp(self):
        self.data = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                     ['region1', 'district1', 'county1', '0.01'],
                     ['region2', 'district2', 'county2', '0.1']]
        self.write_to_csv('wb', self.data)
        self.filename = 'test.csv'
        self.file = open(self.filename, 'rb')

    def tearDown(self):
        os.system("rm -rf %s" % self.filename)

    def test_deletes_one_month_old_error_logs_every_time_an_instance_is_created(self):
        UploadErrorLog.objects.all().delete()
        error_location = UploadErrorLog.objects.create(
            model='LOCATION', filename=self.filename, error="Some errors location")
        error_now = UploadErrorLog.objects.create(
            filename=self.filename, error="Some errors now")
        two_months_old_error_log = UploadErrorLog.objects.create(
            filename=self.filename, error="Some different errors")
        two_months_old_error_log.created = datetime.utcnow().replace(tzinfo=utc) - \
            timedelta(days=31)
        two_months_old_error_log.save()
        UploadService(self.file)
        two_months_old_error_log = UploadErrorLog.objects.filter(
            filename=self.filename, error="Some different errors")
        self.failIf(two_months_old_error_log)
        error_location = UploadErrorLog.objects.filter(
            model='LOCATION', filename=self.filename, error="Some errors location")
        self.failUnless(error_location)
        error_now = UploadErrorLog.objects.filter(
            filename=self.filename, error="Some errors now")
        self.failUnless(error_now)

    def test_error_logging(self):
        UploadErrorLog.objects.all().delete()
        uploader_service = UploadService(self.file)
        uploader_service.log_error(row_number=1, error="hahaha")
        retrieved_log = UploadErrorLog.objects.filter(
            filename=self.file.name, row_number=1, error="hahaha")
        self.assertEqual(1, retrieved_log.count())

    def test_remove_trailing_name_in_headers(self):
        headers = ['heheName', 'somethingCode',
                   'hahaName', 'blablaCode', 'hihihi', 'hohoho']
        self.assertEqual(['hehe', 'somethingCode', 'haha', 'blablaCode', 'hihihi', 'hohoho'],
                         UploadService.remove_trailing('Name', in_array=headers))
        self.assertEqual(['hehe', 'haha', 'hihihi', 'hohoho'],
                         UploadService.remove_trailing('Name', in_array=headers, exclude='Code'))
        self.assertEqual(['hehe', 'haha', 'hihihi', 'hohoho'],
                         UploadService.remove_trailing('Name', headers, 'Code'))
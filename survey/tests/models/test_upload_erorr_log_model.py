from survey.models.upload_error_logs import UploadErrorLog
from survey.tests.base_test import BaseTest


class UploadErrorLogTest(BaseTest):
    def test_fields(self):
        upload_log = UploadErrorLog()
        fields = [str(item.attname) for item in upload_log._meta.fields]
        self.assertEqual(7, len(fields))
        for field in ['id', 'created', 'modified', 'model', 'filename', 'row_number', 'error']:
            self.assertIn(field, fields)

    def test_store(self):
        upload_log = UploadErrorLog.objects.create(model='WEIGHTS', filename='test.csv', row_number=1, error="Location Bukoto in Kampala not found.")
        self.failUnless(upload_log.id)

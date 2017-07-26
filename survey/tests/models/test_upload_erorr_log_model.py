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
        upload_log = UploadErrorLog.objects.create(
            model='WEIGHTS', filename='test.csv', row_number=1, error="Location Bukoto in Kampala not found.")
        self.failUnless(upload_log.id)

    def setUp(self):
        UploadErrorLog.objects.create(model="Kampala",filename="dil",row_number='5',error='wrong')

    def test_backend(self):
        model = UploadErrorLog.objects.get(model="Kampala")
        filename = UploadErrorLog.objects.get(filename="dil")
        row_number = UploadErrorLog.objects.get(row_number="5")
        error = UploadErrorLog.objects.get(error="wrong")       
        self.assertEqual(model.model,'Kampala')        
        self.assertEqual(len(model.model),7)
        self.assertEqual(filename.filename,'dil')        
        self.assertEqual(len(filename.filename),3)
        self.assertEqual(row_number.row_number,5)        
        self.assertEqual(len(str(row_number.row_number)),1)
        self.assertEqual(error.error,'wrong')        
        self.assertEqual(len(error.error),5)

import os

from django.core.files.uploadedfile import SimpleUploadedFile

from survey.forms.upload_locations import UploadLocationForm
from survey.tests.base_test import BaseTest


class UploadLocationFormTest(BaseTest):
    def setUp(self):
        self.filename = 'empty_file'

    def tearDown(self):
        os.system("rm -rf %s"%self.filename)


    def test_should_know_fields(self):
        upload_location_form = UploadLocationForm()

        fields = ['file']

        [self.assertIn(field, upload_location_form.fields) for field in fields]

    def test_empty_file(self):
        data_file={'file': SimpleUploadedFile(self.filename, open(self.filename, 'a').close())}

        upload_location_form = UploadLocationForm({}, data_file )
        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('The submitted file is empty.', upload_location_form.errors['file'])

    def test_not_csv_file(self):
        self.filename = 'not_csv.xls'
        self.generate_non_csv_file(self.filename)
        file = open(self.filename,'rb')
        upload_location_form = UploadLocationForm({}, {'file':SimpleUploadedFile(self.filename, file.read())})
        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('The file extension should be .csv.', upload_location_form.errors['file'])

from random import randint
from django.test import TestCase
from survey.forms.upload_locations import UploadLocationForm
import xlwt
from django.core.files.uploadedfile import SimpleUploadedFile
import os



class UploadLocationFormTest(TestCase):
    def setUp(self):
        self.filename = 'empty_file'

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


    def tearDown(self):
        os.system("rm -rf %s"%self.filename)

    def generate_non_csv_file(self, filename):
        book = xlwt.Workbook()
        sheet1 = book.add_sheet("Sheet 1")
        sheet1.write(0, 0, "Region")
        sheet1.write(0, 1, "District")
        sheet1.write(0, 2, "County")
        size = 3
        for i in xrange(1, size+1):
            for j in xrange(size):
                sheet1.write(i, j, randint(0,100))
        book.save(filename)





import os
from django.core.files import File
from survey.services.csv_uploader import CSV_Uploader
from survey.tests.base_test import BaseTest


class CSVUploaderTest(BaseTest):

    def setUp(self):
        self.filename = 'simple.csv'
        self.data = [["0","1","2"], ["0","1","2"], ["0","1","2"]]
        self.headers = ["Region", "District", "County"]

    def tearDown(self):
        os.system("rm -rf %s"%self.filename)

    def generate_csv_file(self, filename):
        data = [self.headers]
        data.extend(self.data)
        self.write_to_csv('wb', data, filename)

    def test_read_headers_and_data(self):
        self.generate_csv_file(self.filename)
        file = File(open(self.filename, 'rb'))
        headers, data = CSV_Uploader(file).split_content()
        self.assertEqual(self.headers, headers)
        self.assertEqual(self.data, data)

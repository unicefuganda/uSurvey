import os
from django.core.files.uploadedfile import SimpleUploadedFile
from survey.forms.upload_csv_file import UploadEAForm
from survey.models import Survey
from survey.tests.base_test import BaseTest


class UploadEAFormTest(BaseTest):

    def setUp(self):
        self.filename = 'test_uganda.csv'
        self.filedata = [
            ['Regiontype', 'Districttype', 'Counttype',
                'EA',                   'Parishtype', 'EA'],
            ['region1',    'district1',    'county1',
             'ea_containing_parish', 'parish_1',   ''],
            ['region1',    'district1',    'county1',
             'ea_containing_parish', 'parish_1b',  ''],
            ['region2',    'district2',    'county2',   '',
             'parish2',    'ea_under_parish'],
            ['region2',    'district2',    'county2',   '',                     'parish2',    'ea_under_parish']]

        self.write_to_csv('wb', self.filedata, self.filename)

    def tearDown(self):
        os.system("rm -rf %s" % self.filename)

    def test_should_know_fields(self):
        upload_location_form = UploadEAForm()

        fields = ['file', 'survey']

        [self.assertIn(field, upload_location_form.fields) for field in fields]

    def test_empty_survey(self):
        survey = Survey.objects.create(name="not to be used")
        data_file = {'file': SimpleUploadedFile(
            self.filename, open(self.filename, 'rb').close())}

        upload_location_form = UploadEAForm({'survey': ''}, data_file)
        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('This field is required.',
                      upload_location_form.errors['survey'])

    def test_invalid_survey(self):
        Survey.objects.create(name="not to be used")
        data_file = {'file': SimpleUploadedFile(
            self.filename, open(self.filename, 'rb').close())}
        invalid_survey_id = '1121'

        upload_location_form = UploadEAForm(
            {'survey': invalid_survey_id}, data_file)
        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('Select a valid choice. That choice is not one of the available choices.',
                      upload_location_form.errors['survey'])

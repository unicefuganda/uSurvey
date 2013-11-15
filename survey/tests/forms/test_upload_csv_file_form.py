import os

from django.core.files.uploadedfile import SimpleUploadedFile
from survey.models import Survey

from survey.services.location_upload import UploadLocation
from survey.forms.upload_csv_file import UploadCSVFileForm, UploadWeightsForm
from survey.tests.base_test import BaseTest


class UploadCSVFileFormTest(BaseTest):
    def setUp(self):
        self.filename = 'empty_file'

    def tearDown(self):
        os.system("rm -rf %s"%self.filename)

    def test_should_know_fields(self):
        upload_location_form = UploadCSVFileForm(uploader=UploadLocation)

        fields = ['file']

        [self.assertIn(field, upload_location_form.fields) for field in fields]

    def test_empty_file(self):
        data_file={'file': SimpleUploadedFile(self.filename, open(self.filename, 'a').close())}

        upload_location_form = UploadCSVFileForm(UploadLocation, {}, data_file)
        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('The submitted file is empty.', upload_location_form.errors['file'])

    def test_not_csv_file(self):
        self.filename = 'not_csv.xls'
        self.generate_non_csv_file(self.filename)
        file = open(self.filename,'rb')
        upload_location_form = UploadCSVFileForm(UploadLocation, {}, {'file':SimpleUploadedFile(self.filename, file.read())})
        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('The file extension should be .csv.', upload_location_form.errors['file'])


class UploadLocationWeightsFormTest(BaseTest):
    def setUp(self):
        self.filename = 'test_uganda.csv'
        self.filedata = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                            ['region1',  'district1', 'county1', '0.01'],
                            ['region2', 'district2', 'county2', '0.1']]
        self.write_to_csv('wb', self.filedata, self.filename)

    def tearDown(self):
        os.system("rm -rf %s"%self.filename)

    def test_should_know_fields(self):
        upload_location_form = UploadWeightsForm()

        fields = ['file', 'survey']

        [self.assertIn(field, upload_location_form.fields) for field in fields]

    def test_empty_survey(self):
        survey = Survey.objects.create(name="not to be used")
        data_file={'file': SimpleUploadedFile(self.filename, open(self.filename, 'rb').close())}

        upload_location_form = UploadWeightsForm({'survey':''}, data_file)
        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('This field is required.', upload_location_form.errors['survey'])

    def test_invalid_survey(self):
        Survey.objects.create(name="not to be used")
        data_file = {'file': SimpleUploadedFile(self.filename, open(self.filename, 'rb').close())}
        invalid_survey_id ='1121'

        upload_location_form = UploadWeightsForm({'survey': invalid_survey_id}, data_file)
        self.assertEqual(False, upload_location_form.is_valid())
        self.assertIn('Select a valid choice. That choice is not one of the available choices.', upload_location_form.errors['survey'])

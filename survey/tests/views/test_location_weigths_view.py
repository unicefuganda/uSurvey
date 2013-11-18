from django.contrib.auth.models import User
from django.test import Client
from mock import patch
from rapidsms.contrib.locations.models import Location, LocationType
from survey.forms.upload_csv_file import UploadWeightsForm
from survey.models import LocationWeight, Survey, UploadErrorLog
from survey.tests.base_test import BaseTest
from survey.views.location_widget import LocationWidget


class UploadWeightsTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')

        self.reqion_type = LocationType.objects.create(name="region1", slug="region1")
        self.district_type = LocationType.objects.create(name="district1", slug='district1')
        self.county_type = LocationType.objects.create(name="county1", slug='county1')


        region = Location.objects.create(name="region1", type=self.reqion_type)
        district = Location.objects.create(name="district1", tree_parent=region, type=self.district_type)
        Location.objects.create(name="county1", tree_parent=district, type=self.county_type)

        region = Location.objects.create(name="region2", type=self.reqion_type)
        district = Location.objects.create(name="district2", tree_parent=region, type=self.district_type)
        Location.objects.create(name="county2", tree_parent=district, type=self.county_type)

        self.filename = 'test_uganda.csv'
        self.filedata = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                            ['region1',  'district1', 'county1', '0.01'],
                            ['region2', 'district2', 'county2', '0.1']]
        self.write_to_csv('wb', self.filedata, self.filename)
        self.file = open(self.filename, 'rb')

        self.survey = Survey.objects.create(name="Survey")

    def test_should_return_success_and_render_template(self):
        response = self.client.get('/locations/weights/upload/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('locations/weights/upload.html', templates)

    def test_should_render_context_data(self):
        response = self.client.get('/locations/weights/upload/')
        self.assertEqual(response.context['button_label'], "Upload")
        self.assertEqual(response.context['id'], "upload-location-weights-form")
        self.assertEqual(len(response.context['location_types']), 3)
        expected_types = [self.reqion_type, self.district_type, self.county_type]
        [self.assertIn(_type, response.context['location_types']) for _type in expected_types]
        self.assertIsInstance(response.context['upload_form'], UploadWeightsForm)

    def test_should_redirect_after_post(self):
        data = {'file': self.file,
                'survey': self.survey.id}
        response = self.client.post("/locations/weights/upload/", data=data)
        self.assertRedirects(response, '/locations/weights/upload/', status_code=302, target_status_code=200, msg_prefix='')

    @patch('survey.services.location_weights_upload.UploadLocationWeights.upload')
    def test_should_give_uploading_message(self, mock_upload):
        data = {'file': self.file,
                'survey': self.survey.id}
        response = self.client.post('/locations/weights/upload/', data=data)
        assert mock_upload.called
        self.assertIn('Upload in progress. This could take a while.', response.cookies['messages'].value)

    def test_should_upload_csv_sucess(self):
        data = {'file': self.file,
                'survey': self.survey.id}
        response = self.client.post('/locations/weights/upload/', data=data)

        for row in self.filedata[1:]:
            location = Location.objects.get(name=row[-2], tree_parent__name=row[-3])
            self.failUnless(LocationWeight.objects.filter(location=location, selection_probability=row[-1]))
            parents_names = location.get_ancestors().values_list('name', flat=True)
            [self.assertIn(location_name, parents_names) for location_name in row[0:-2]]

    def test_upload_csv_failure_if_selection_probability_is_NaN(self):
        filedata = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                            ['region1',  'district1', 'county1', 'bla bli blo not a number'],
                            ['region2', 'district2', 'county2', '0.1']]
        self.write_to_csv('wb', filedata, self.filename)
        file = open(self.filename, 'rb')

        data = {'file': file,
                'survey': self.survey.id}

        row = filedata[1]
        location = Location.objects.get(name=row[-2], tree_parent__name=row[-3])
        LocationWeight.objects.filter(location=location).delete()
        response = self.client.post('/locations/weights/upload/', data=data)
        self.failIf(LocationWeight.objects.filter(location=location))

        location = Location.objects.get(name="county2", tree_parent__name="district2")
        self.failUnless(LocationWeight.objects.filter(location=location, selection_probability=0.1))

    def test_assert_restricted_permissions(self):
        self.assert_login_required('/locations/weights/upload/')
        self.assert_restricted_permission_for('/locations/weights/upload/')

    def test_should_get_list_and_returns_success_with_template(self):
        country = LocationType.objects.create(name="Country", slug="country")
        region = Location.objects.create(name="region1", type=self.reqion_type)
        district = Location.objects.create(name="district1", tree_parent=region, type=self.district_type)
        county = Location.objects.create(name="county1", tree_parent=district, type=self.county_type)

        region1 = Location.objects.create(name="region2", type=self.reqion_type)
        district1 = Location.objects.create(name="district2", tree_parent=region1, type=self.district_type)
        county1 = Location.objects.create(name="county2", tree_parent=district1, type=self.county_type)
        location_weight_1 = LocationWeight.objects.create(location=county, selection_probability=0.1, survey=self.survey)
        location_weight_2 = LocationWeight.objects.create(location=county1, selection_probability=0.2, survey=self.survey)

        response = self.client.get('/locations/weights/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('locations/weights/index.html', templates)

        self.assertIn(location_weight_1, response.context['location_weights'])
        self.assertIn(location_weight_2, response.context['location_weights'])
        expected_location_types = [self.reqion_type, self.district_type, self.county_type]
        [self.assertIn(_type, response.context['location_types']) for _type in expected_location_types]
        self.assertNotIn(country, response.context['location_types'])

        self.assertIsInstance(response.context['location_data'], LocationWidget)
        self.assertEqual(1, len(response.context['surveys']))
        self.assertIn(self.survey, response.context['surveys'])
        self.assertIsNone(response.context['selected_survey'])

    def test_filter_list_weights_by_location(self):
        district = Location.objects.create(name="district1", type=self.district_type)
        county = Location.objects.create(name="county1", tree_parent=district, type=self.county_type)

        region1 = Location.objects.create(name="region2", type=self.reqion_type)
        district1 = Location.objects.create(name="district2", tree_parent=region1, type=self.district_type)
        county1 = Location.objects.create(name="county2", tree_parent=district1, type=self.county_type)
        weight_1 = LocationWeight.objects.create(location=county, selection_probability=0.1, survey=self.survey)
        weight_2 = LocationWeight.objects.create(location=county1, selection_probability=0.2, survey=self.survey)

        response = self.client.get('/locations/weights/?location=%d' % county1.id)

        self.assertEqual(1, len(response.context['location_weights']))
        self.assertIn(weight_2, response.context['location_weights'])
        self.assertIsNone(response.context['selected_survey'])

    def test_filter_list_weights_by_survey(self):
        hoho_survey = Survey.objects.create(name="what hohoho")
        district = Location.objects.create(name="district1", type=self.district_type)
        county = Location.objects.create(name="county1", tree_parent=district, type=self.county_type)

        region1 = Location.objects.create(name="region2", type=self.reqion_type)
        district1 = Location.objects.create(name="district2", tree_parent=region1, type=self.district_type)
        county1 = Location.objects.create(name="county2", tree_parent=district1, type=self.county_type)
        weight_1 = LocationWeight.objects.create(location=county, selection_probability=0.1, survey=self.survey)
        weight_2 = LocationWeight.objects.create(location=county1, selection_probability=0.2, survey=hoho_survey)

        response = self.client.get('/locations/weights/?survey=%d' % self.survey.id)

        self.assertEqual(1, len(response.context['location_weights']))
        self.assertIn(weight_1, response.context['location_weights'])
        self.assertEqual(self.survey, response.context['selected_survey'])
        self.assertEqual(2, len(response.context['surveys']))
        self.assertIn(self.survey, response.context['surveys'])
        self.assertIn(hoho_survey, response.context['surveys'])

        self.assertIn('list_weights_page', response.context['action'])


    def test_filter_list_weights_by_location_and_survey(self):
        hoho_survey = Survey.objects.create(name="what hohoho")
        district = Location.objects.create(name="district1", type=self.district_type)
        county = Location.objects.create(name="county1", tree_parent=district, type=self.county_type)

        region1 = Location.objects.create(name="region2", type=self.reqion_type)
        district1 = Location.objects.create(name="district2", tree_parent=region1, type=self.district_type)
        county1 = Location.objects.create(name="county2", tree_parent=district1, type=self.county_type)
        weight_1 = LocationWeight.objects.create(location=county, selection_probability=0.1, survey=self.survey)
        weight_2 = LocationWeight.objects.create(location=county1, selection_probability=0.2, survey=self.survey)

        response = self.client.get('/locations/weights/?survey=%d&location=%d' % (self.survey.id, county1.id))

        self.assertEqual(1, len(response.context['location_weights']))
        self.assertIn(weight_2, response.context['location_weights'])
        self.assertEqual(self.survey, response.context['selected_survey'])
        self.assertEqual(2, len(response.context['surveys']))
        self.assertIn(self.survey, response.context['surveys'])
        self.assertIn(hoho_survey, response.context['surveys'])


class UploadWeightsErrorLogTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')

        region = Location.objects.create(name="region1")
        district = Location.objects.create(name="district1", tree_parent=region)
        Location.objects.create(name="county1", tree_parent=district)

        region = Location.objects.create(name="region2")
        district = Location.objects.create(name="district2", tree_parent=region)
        Location.objects.create(name="county2", tree_parent=district)

        self.filename = 'test_uganda.csv'
        self.filedata = [['RegionName', 'DistrictName', 'CountyName', 'Selection Probability'],
                            ['region1',  'district1', 'county1', '0.01'],
                            ['region2', 'district2', 'county2', '0.1']]
        self.write_to_csv('wb', self.filedata, self.filename)
        self.file = open(self.filename, 'rb')

        self.survey = Survey.objects.create(name="Survey")

    def test_should_get_list_and_returns_success_with_template(self):
        error_log = UploadErrorLog.objects.create(model="WEIGHTS", error="Some error", filename="Some file", row_number=1)
        error_log_1 = UploadErrorLog.objects.create(model="LOCATION", error="Some error", filename="Some file", row_number=25)
        error_log_2 = UploadErrorLog.objects.create(model="WEIGHTS", error="Some error_2", filename="Some file", row_number=25)
        response = self.client.get('/locations/weights/error_logs/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('locations/weights/error_logs.html', templates)

        expected_errors = [error_log, error_log_2]
        [self.assertIn(error, response.context['error_logs']) for error in expected_errors]
        self.assertNotIn(error_log_1, response.context['error_logs'])
        self.assertIsNotNone(response.context['request'])

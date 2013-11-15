from django.contrib.auth.models import User
from django.test import Client
from mock import patch
from rapidsms.contrib.locations.models import Location, LocationType
from survey.forms.upload_csv_file import UploadWeightsForm
from survey.models import LocationWeight, Survey
from survey.tests.base_test import BaseTest


class UploadWeightsTest(BaseTest):
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

    def test_should_return_success_and_render_template(self):
        response = self.client.get('/locations/weights/upload/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('locations/weights/upload.html', templates)

    def test_should_render_context_data(self):
        type = LocationType.objects.create(name="country", slug="country")
        response = self.client.get('/locations/weights/upload/')
        self.assertEqual(response.context['button_label'], "Upload")
        self.assertEqual(response.context['id'], "upload-location-weights-form")
        self.assertEqual(len(response.context['location_types']), 1)
        self.assertIn(type, response.context['location_types'])
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

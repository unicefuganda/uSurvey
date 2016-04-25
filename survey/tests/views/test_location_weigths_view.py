import datetime
from django.contrib.auth.models import User
from django.test import Client
from mock import patch
from survey.models.locations import *
from survey.forms.upload_csv_file import UploadWeightsForm
from survey.models import LocationWeight, Survey, UploadErrorLog, LocationTypeDetails
from survey.tests.base_test import BaseTest
from survey.views.location_widget import LocationWidget
from django.utils.timezone import utc


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

        LocationTypeDetails.objects.create(country=region, location_type=self.reqion_type)
        LocationTypeDetails.objects.create(country=region, location_type=self.district_type)
        LocationTypeDetails.objects.create(country=region, location_type=self.county_type)


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

    def test_assert_restricted_permissions(self):
        self.assert_login_required('/locations/weights/upload/')
        self.assert_restricted_permission_for('/locations/weights/upload/')

class UploadWeightsErrorLogTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')
        self.region_type = LocationType.objects.create(name="region1", slug="region1")
        self.district_type = LocationType.objects.create(name="district1", slug='district1')
        region = Location.objects.create(name="region1",type=self.region_type)
        district = Location.objects.create(name="district1", parent=region,type=self.district_type)
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

        today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.assertEqual(today, response.context['selected_from_date'])
        self.assertEqual(today, response.context['selected_to_date'])


    def test_should_filter_to_and_from_dates(self):
        error_log = UploadErrorLog.objects.create(model="WEIGHTS", error="Some error", filename="Some file", row_number=1)
        error_log_1 = UploadErrorLog.objects.create(model="LOCATION", error="Some error", filename="Some file", row_number=25)
        error_log_2 = UploadErrorLog.objects.create(model="WEIGHTS", error="Some error_2", filename="Some file", row_number=25)

        error_log_2.created = error_log_2.created.replace(tzinfo=utc) + datetime.timedelta(days=4)
        error_log_2.save()

        error_log_created = error_log.created.strftime('%Y-%m-%d')

        response = self.client.get('/locations/weights/error_logs/?from_date=%s&to_date=%s'%(error_log_created, error_log_created))
        self.assertEqual(200, response.status_code)


        self.assertEqual(0, response.context['error_logs'].count())
        # self.assertIn(error_log, response.context['error_logs'])
        self.assertEqual(error_log.created.replace(hour=0, minute=0, second=0, microsecond=0), response.context['selected_from_date'])
        self.assertEqual(error_log.created.replace(hour=0, minute=0, second=0, microsecond=0), response.context['selected_to_date'])

    def test_assert_restricted_permissions(self):
        self.assert_login_required('/locations/weights/')
        self.assert_restricted_permission_for('/locations/weights/')
        self.assert_restricted_permission_for('/locations/weights/error_logs/')

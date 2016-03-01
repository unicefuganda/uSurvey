from django.contrib.auth.models import User
from django.test import Client
from mock import patch
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models.locations import *
from survey.forms.upload_csv_file import UploadEAForm
from survey.models import Survey, LocationTypeDetails, EnumerationArea
from survey.services.ea_upload import UploadEACSVLayoutHelper
from survey.tests.base_test import BaseTest
from django.utils.timezone import utc


class UploadWeightsTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')

        self.country = LocationType.objects.create(name='Country', slug='country')
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.country)

        self.district_type = LocationType.objects.create(name="Districttype", slug='districttype')
        self.county_type = LocationType.objects.create(name="Countytype", slug='countytype')
        self.parish_type = LocationType.objects.create(name="Parishtype", slug='parishtype')

        self.district = Location.objects.create(name="district1", tree_parent=self.country, type=self.district_type)
        self.county_1 = Location.objects.create(name="county1", tree_parent=self.district, type=self.county_type)
        self.parish_1 = Location.objects.create(name="parish_1", tree_parent=self.county_1, type=self.parish_type)
        self.parish_1_b = Location.objects.create(name="parish_1b", tree_parent=self.county_1, type=self.parish_type)

        self.district = Location.objects.create(name="district2", tree_parent=self.country, type=self.district_type)
        self.county_2 = Location.objects.create(name="county2", tree_parent=self.district, type=self.county_type)
        self.parish_2 = Location.objects.create(name="parish_2", tree_parent=self.county_2, type=self.parish_type)

        self.filedata = [
                ['Regiontype', 'Districttype', 'Counttype', 'EA',                   'Parishtype', 'EA'],
                ['region1',    'district1',    'county1',   'ea_containing_parish', 'parish_1',   ''],
                ['region1',    'district1',    'county1',   'ea_containing_parish', 'parish_1b',  ''],
                ['region2',    'district2',    'county2',   '',                     'parish_2',    'ea_under_parish'],
                ['region2',    'district2',    'county2',   '',                     'parish_2',    'ea_under_parish']]

        self.filename = 'test_uganda.csv'
        self.write_to_csv('wb', self.filedata, self.filename)

        self.file = open(self.filename, 'rb')

        self.survey = Survey.objects.create(name="Survey")

    def test_should_return_success_and_render_template(self):
        response = self.client.get('/locations/enumeration_area/upload/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('locations/enumeration_area/upload.html', templates)

    def test_should_render_context_data(self):
        response = self.client.get('/locations/enumeration_area/upload/')
        self.assertEqual(response.context['button_label'], "Upload")
        self.assertEqual(response.context['id'], "upload-location-ea-form")
        self.assertIsInstance(response.context['csv_layout'], UploadEACSVLayoutHelper)
        self.assertIsInstance(response.context['upload_form'], UploadEAForm)

    # def test_should_redirect_after_post(self):
    #     data = {'file': self.file,
    #             'survey': self.survey.id}
    #     response = self.client.post("/locations/enumeration_area/upload/", data=data)
    #     self.assertRedirects(response, '/locations/enumeration_area/upload/', status_code=302, target_status_code=200, msg_prefix='')
    #
    # @patch('survey.services.ea_upload.UploadEA.upload')
    # def test_should_give_uploading_message(self, mock_upload):
    #     data = {'file': self.file,
    #             'survey': self.survey.id}
    #     response = self.client.post('/locations/enumeration_area/upload/', data=data)
    #     assert mock_upload.called
    #     self.assertIn('Upload in progress. This could take a while.', response.cookies['messages'].value)
    #
    # def test_should_upload_csv_sucess(self):
    #     data = {'file': self.file,
    #             'survey': self.survey.id}
    #     response = self.client.post('/locations/enumeration_area/upload/', data=data)
    #
    #     for row in self.filedata[1:]:
    #         first_ea_column_index = -3
    #         second_ea_column_index = -1
    #         ea_name = row[first_ea_column_index] or row[second_ea_column_index]
    #         retrieved_ea = EnumerationArea.objects.filter(name=ea_name)
    #         self.failUnless(retrieved_ea)
    #
    #         lowest_location_level_index = -2
    #         second_lowest_location_level_index = -4
    #         location = Location.objects.get(name=row[lowest_location_level_index],
    #                                         tree_parent__name=row[second_lowest_location_level_index])
    #         self.assertIn(location, retrieved_ea[0].locations.all())
    #
    #         parents_names = location.get_ancestors().values_list('name', flat=True)
    #         [self.assertIn(location_name, parents_names) for location_name in row[0:first_ea_column_index]]

    # def test_upload_csv_failure_if_EA_name_is_missing(self):
    #     EMPTY_EA_NAME = ''
    #     filedata = [
    #             ['Regiontype', 'Districttype', 'Counttype', 'EA',                   'Parishtype', 'EA'],
    #             ['region1',    'district1',    'county1',   EMPTY_EA_NAME,          'parish_1',   ''],
    #             ['region1',    'district1',    'county1',   'ea_containing_parish', 'parish_1b',  ''],
    #             ['region2',    'district2',    'county2',   '',                     'parish_2',    'ea_under_parish'],
    #             ['region2',    'district2',    'county2',   '',                     'parish_2',    'ea_under_parish']]
    #
    #     self.write_to_csv('wb', filedata, self.filename)
    #     file = open(self.filename, 'rb')
    #
    #     data = {'file': file,
    #             'survey': self.survey.id}
    #
    #     row = filedata[1]
    #     first_ea_column_index = -3
    #     second_ea_column_index = -1
    #     ea_name = row[first_ea_column_index] or row[second_ea_column_index]
    #     retrieved_ea = EnumerationArea.objects.filter(name=ea_name, survey_allocations=self.survey)
    #     self.failIf(retrieved_ea)
    #
    #     response = self.client.post('/locations/enumeration_area/upload/', data=data)
    #
    #     self.failIf(EnumerationArea.objects.filter(name=ea_name, survey_allocations=self.survey))
    #
    #     row = filedata[2]
    #     first_ea_column_index = -3
    #     second_ea_column_index = -1
    #     ea_name = row[first_ea_column_index] or row[second_ea_column_index]
    #     retrieved_ea = EnumerationArea.objects.filter(name=ea_name, survey_allocations=self.survey)
    #     # self.failUnless(retrieved_ea)
    #
    #     lowest_location_level_index = -2
    #     second_lowest_location_level_index = -4
    #     location = Location.objects.get(name=row[lowest_location_level_index],
    #                                     tree_parent__name=row[second_lowest_location_level_index])
    #     self.assertIn(location, retrieved_ea[0].locations.all())

    # def test_upload_csv_failure_if_EA_name_is_missing(self):
    #     EMPTY_EA_NAME = ''
    #     filedata = [
    #             ['Regiontype', 'Districttype', 'Counttype', 'EA',                   'Parishtype', 'EA'],
    #             ['region1',    'district1',    'county1',   EMPTY_EA_NAME,          'parish_1',   ''],
    #             ['region1',    'district1',    'county1',   'ea_containing_parish', 'parish_1b',  ''],
    #             ['region2',    'district2',    'county2',   '',                     'parish_2',    'ea_under_parish'],
    #             ['region2',    'district2',    'county2',   '',                     'parish_2',    'ea_under_parish']]
    #
    #     self.write_to_csv('wb', filedata, self.filename)
    #     file = open(self.filename, 'rb')
    #
    #     data = {'file': file,
    #             'survey': self.survey.id}
    #
    #     row = filedata[1]
    #     first_ea_column_index = -3
    #     second_ea_column_index = -1
    #     ea_name = row[first_ea_column_index] or row[second_ea_column_index]
    #     retrieved_ea = EnumerationArea.objects.filter(name=ea_name, survey_allocations=self.survey)
    #     self.failIf(retrieved_ea)
    #
    #     response = self.client.post('/locations/enumeration_area/upload/', data=data)
    #
    #     self.failIf(EnumerationArea.objects.filter(name=ea_name, survey_allocations=self.survey))
    #
    #     row = filedata[2]
    #     first_ea_column_index = -3
    #     second_ea_column_index = -1
    #     ea_name = row[first_ea_column_index] or row[second_ea_column_index]
    #     retrieved_ea = EnumerationArea.objects.filter(name=ea_name, survey_allocations=self.survey)
    #
    #
    #     lowest_location_level_index = -2
    #     second_lowest_location_level_index = -4
    #     location = Location.objects.get(name=row[lowest_location_level_index],
    #                                     tree_parent__name=row[second_lowest_location_level_index])
    #     self.assertIn(location, retrieved_ea[0].locations.all())



    def test_assert_restricted_permissions(self):
        self.assert_restricted_permission_for('/locations/enumeration_area/upload/')

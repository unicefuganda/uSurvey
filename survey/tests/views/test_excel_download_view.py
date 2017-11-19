from datetime import date, datetime
from django.template.defaultfilters import slugify
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from survey.models.locations import *
from survey.forms.filters import SurveyBatchFilterForm
from survey.models import EnumerationArea, QuestionModule
from survey.models.batch import Batch
from survey.models.backend import Backend
from survey.models.interviewer import Interviewer
from survey.models.questions import Question, QuestionOption
from survey.models.surveys import Survey
from survey.tests.base_test import BaseTest
from django.http.request import QueryDict, MultiValueDict
import django_rq
from django.core.urlresolvers import reverse


class ExcelDownloadViewTest(BaseTest):

    def test_get(self):
        client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(
            codename='can_view_aggregates', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)
        self.client.login(username='Rajni', password='I_Rock')
        Survey.objects.create(name="survey")
        response = self.client.get('/aggregates/download_spreadsheet')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/download_excel.html', templates)
        self.assertIsInstance(
            response.context['survey_batch_filter_form'], SurveyBatchFilterForm)

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for(
            '/aggregates/download_spreadsheet')

    # def test_excel_download(self):
    #     country = LocationType.objects.create(name='Country', slug='country')
    #     uganda = Location.objects.create(name="Uganda", type=country)
    #     # LocationTypeDetails.objects.create(
    #     #     country=uganda, location_type=country)
    #     district_type = LocationType.objects.create(
    #         name="Districttype", slug='districttype', parent=country)
    #     county_type = LocationType.objects.create(
    #         name="Countytype", slug='countytype', parent=district_type)
    #     subcounty_type = LocationType.objects.create(
    #         name="subcountytype", slug='subcountytype', parent=county_type)
    #     parish_type = LocationType.objects.create(
    #         name="Parishtype", slug='parishtype', parent=county_type)
    #     district = Location.objects.create(
    #         name="district1", parent=uganda, type=district_type)
    #     county_1 = Location.objects.create(
    #         name="county1", parent=district, type=county_type)
    #     subcounty_1 = Location.objects.create(
    #         name="subcounty_1", parent=county_1, type=subcounty_type)
    #     parish_1 = Location.objects.create(
    #         name="parish_1", parent=subcounty_1, type=parish_type)
    #     survey = Survey.objects.create(name='survey name', description='survey descrpition',
    #                                         sample_size=10)
    #     batch = Batch.objects.create(order=1, name="Batch A", survey=survey)
    #     client = Client()
    #     raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
    #     user_without_permission = User.objects.create_user(
    #         username='useless', email='rajni@kant.com', password='I_Suck')
    #     some_group = Group.objects.create(name='some group')
    #     auth_content = ContentType.objects.get_for_model(Permission)
    #     permission, out = Permission.objects.get_or_create(
    #         codename='can_view_aggregates', content_type=auth_content)
    #     some_group.permissions.add(permission)
    #     some_group.user_set.add(raj)
    #     self.client.login(username='Rajni', password='I_Rock')
    #     # url = '/aggregates/spreadsheet_report/?District=&County=&Subcounty=&Parish=&survey=%d&batch=%d&multi_option=1&action=Download+Spreadsheet' % (
    #     #     survey.id, batch.id)
    #     # response = self.client.get(url)
    #     # self.client.get(reverse('excel_report'))
    #     # self.assertIn(response.status_code, [200,302])
    #     rq_queues = django_rq.get_queue('results-queue')
    #     keys = rq_queues.connection.keys()
    #     self.assertIn('rq:workers', keys)

    # def test_email(self):
    #     country = LocationType.objects.create(name='Country', slug='country')
    #     uganda = Location.objects.create(name="Uganda", type=country)
    #     # LocationTypeDetails.objects.create(
    #     #     country=uganda, location_type=country)
    #     district_type = LocationType.objects.create(
    #         name="Districttype", slug='districttype', parent=country)
    #     county_type = LocationType.objects.create(
    #         name="Countytype", slug='countytype', parent=district_type)
    #     subcounty_type = LocationType.objects.create(
    #         name="subcountytype", slug='subcountytype', parent=county_type)
    #     parish_type = LocationType.objects.create(
    #         name="Parishtype", slug='parishtype', parent=county_type)
    #     district = Location.objects.create(
    #         name="district1", parent=uganda, type=district_type)
    #     county_1 = Location.objects.create(
    #         name="county1", parent=district, type=county_type)
    #     subcounty_1 = Location.objects.create(
    #         name="subcounty_1", parent=county_1, type=subcounty_type)
    #     parish_1 = Location.objects.create(
    #         name="parish_1", parent=subcounty_1, type=parish_type)
    #     survey = Survey.objects.create(name='survey nam1e', description='survey descrpition',
    #                                         sample_size=10)
    #     batch = Batch.objects.create(order=11, name="Batch 1A", survey=survey)
    #     client = Client()
    #     raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
    #     user_without_permission = User.objects.create_user(
    #         username='useless', email='rajni@kant.com', password='I_Suck')
    #     some_group = Group.objects.create(name='some group')
    #     auth_content = ContentType.objects.get_for_model(Permission)
    #     permission, out = Permission.objects.get_or_create(
    #         codename='can_view_aggregates', content_type=auth_content)
    #     some_group.permissions.add(permission)
    #     some_group.user_set.add(raj)
    #     self.client.login(username='Rajni', password='I_Rock')
    #     # url = '/aggregates/spreadsheet_report/?District=&County=&Subcounty=&Parish=&survey=%d&batch=%d&multi_option=1&action=Email+Spreadsheet' % (
    #     #     survey.id, batch.id)
    #     # response = self.client.get(url)
    #     # self.client.get(reverse('excel_report'))
    #     # self.assertIn(response.status_code, [200,302])
    #     keys = django_rq.get_queue('results-queue').connection.keys()
    #     self.assertIn('rq:workers', keys)
    #     self.assertNotIn("testkey", keys)


class ReportForCompletedInvestigatorTest(BaseTest):

    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        self.question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        self.survey = Survey.objects.create(name='some group')
        self.batch = Batch.objects.create(name='BatchA', survey=self.survey)
        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(
            codename='can_view_aggregates', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)
        self.client.login(username='Rajni', password='I_Rock')

    def test_should_have_header_fields_in_download_report(self):
        survey = Survey.objects.create(name='some survey')
        file_name = "interviewer.csv"
        response = self.client.post(
            '/interviewers/completed/download/', {'survey': survey.id})
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.get('Content-Type'), "text/csv")
        self.assertEquals(response.get('Content-Disposition'),
                          'attachment; filename="%s"' % file_name)
        row1 = ['Interviewer', 'Access Channels']
        row1.extend(
            list(LocationType.objects.all().values_list('name', flat=True)))
        contents = "%s\r\n" % (",".join(row1))
        self.assertEquals(contents, response.content)

    def test_restricted_permission(self):
        self.assert_login_required('/interviewers/completed/download/')
        self.assert_restricted_permission_for(
            '/interviewers/completed/download/')
        self.assert_restricted_permission_for('/interviewer_report/')

    def test_should_get_view_for_download(self):
        response = self.client.get('/interviewer_report/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/download_interviewer.html', templates)
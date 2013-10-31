from datetime import date
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission

from django.contrib.contenttypes.models import ContentType
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import GroupCondition, HouseholdMemberGroup
from survey.models.batch import Batch
from survey.models.households import HouseholdHead, Household
from survey.models.backend import Backend
from survey.models.investigator import Investigator

from survey.models.question import Question, QuestionOption
from survey.models.surveys import Survey
from survey.tests.base_test import BaseTest


class ExcelDownloadTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)

        self.batch = Batch.objects.create(order = 1, name="BATCH A")
        self.question_1 = Question.objects.create(text="How many members are there in this household?", answer_type=Question.NUMBER, order=1, identifier="QUESTION_1", group=self.member_group)
        self.question_2 = Question.objects.create(text="How many members are there in this household?", answer_type=Question.MULTICHOICE, order=2, identifier="QUESTION_2", group=self.member_group)
        self.question_1.batches.add(self.batch)
        self.question_2.batches.add(self.batch)
        self.option_1_1 = QuestionOption.objects.create(question=self.question_2, text="OPTION 1", order=1)
        self.option_1_2 = QuestionOption.objects.create(question=self.question_2, text="OPTION 2", order=2)
        self.option_1_3 = QuestionOption.objects.create(question=self.question_2, text="Others", order=3)
        sub_question_1 = Question.objects.create(text="Describe the source of drinking water", answer_type=Question.TEXT, subquestion=True, parent=self.question_2, group=self.member_group)
        sub_question_1.batches.add(self.batch)

        self.question_3 = Question.objects.create(text="How many of them are male?", answer_type=Question.TEXT, order=3, identifier="QUESTION_3", group=self.member_group)
        self.question_3.batches.add(self.batch)
        self.investigator = Investigator.objects.create(name="investigator name", mobile_number="123", location=Location.objects.create(name="Kampala"), backend = Backend.objects.create(name='something'))
        self.household = Household.objects.create(investigator=self.investigator, uid=0)
        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname", date_of_birth=date(2000, 9, 1))

        self.investigator.member_answered(self.question_1, self.household_head, answer=1, batch=self.batch)
        self.investigator.member_answered(self.question_2, self.household_head, answer=1, batch=self.batch)
        self.investigator.member_answered(self.question_3, self.household_head, answer="ANSWER", batch=self.batch)

        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_aggregates')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        self.client.login(username='Rajni', password='I_Rock')


    def test_downloaded_excel_file(self):
        file_name = "%s.csv" % self.batch.name
        response = self.client.post('/aggregates/spreadsheet_report', data={'batch': self.batch.pk})
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.get('Content-Type'), "text/csv")
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="%s"' % file_name)

        row1 = ['Location', 'Household Head Name', 'QUESTION_1', 'QUESTION_2', '', 'QUESTION_3']
        row2 = ['Kampala',  'Surname',             '1',            '1',            'OPTION 1', 'ANSWER']

        contents = "%s\r\n%s\r\n" % (",".join(row1), ",".join(row2))

        self.assertEquals(contents, response.content)

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/aggregates/spreadsheet_report')

class ExcelDownloadViewTest(TestCase):

    def test_get(self):
        client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_aggregates', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)

        self.client.login(username='Rajni', password='I_Rock')

        response = self.client.get('/aggregates/download_spreadsheet')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/download_excel.html', templates)
        self.assertEquals(len(response.context['batches']), 0)

    def assert_restricted_permission_for(self, url):
        self.client.logout()

        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)

        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%url, status_code=302, target_status_code=200, msg_prefix='')

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/aggregates/download_spreadsheet')

class ReportForCompletedInvestigatorTest(BaseTest):
    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_aggregates', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)

        self.client.login(username='Rajni', password='I_Rock')

    def test_should_have_header_fields_in_download_report(self):
        survey = Survey.objects.create(name='some survey')
        file_name = "investigator.csv"
        response = self.client.post('/completed_investigators/download/',{'survey':survey.id})
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.get('Content-Type'), "text/csv")
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="%s"' % file_name)
        row1 = ['Investigator', 'Phone Number']
        row1.extend([loc.name for loc in LocationType.objects.all()])
        contents = "%s\r\n" % (",".join(row1))
        self.assertEquals(contents, response.content)

    def test_restricted_permission(self):
        self.assert_login_required('/completed_investigators/download/')
        self.assert_restricted_permission_for('/completed_investigators/download/')

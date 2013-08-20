from django.test import TestCase
from django.test.client import Client
from survey.models import *
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

class ExcelDownloadTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.batch = Batch.objects.create(order = 1, name="BATCH A")
        indicator = Indicator.objects.create(batch=self.batch, order=1, identifier="IDENTIFIER")
        self.question_1 = Question.objects.create(indicator=indicator, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        self.question_2 = Question.objects.create(indicator=indicator, text="How many members are there in this household?", answer_type=Question.MULTICHOICE, order=2)
        self.option_1_1 = QuestionOption.objects.create(question=self.question_2, text="OPTION 1", order=1)
        self.option_1_2 = QuestionOption.objects.create(question=self.question_2, text="OPTION 2", order=2)
        self.option_1_3 = QuestionOption.objects.create(question=self.question_2, text="Others", order=3)
        sub_question_1 = Question.objects.create(indicator=indicator, text="Describe the source of drinking water", answer_type=Question.TEXT, subquestion=True, parent=self.question_2)

        self.question_3 = Question.objects.create(indicator=indicator, text="How many of them are male?", answer_type=Question.TEXT, order=3)
        self.investigator = Investigator.objects.create(name="investigator name", mobile_number="123", location=Location.objects.create(name="Kampala"), backend = Backend.objects.create(name='something'))
        self.household = Household.objects.create(investigator=self.investigator)
        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname")

        self.investigator.answered(self.question_1, self.household, answer=1)
        self.investigator.answered(self.question_2, self.household, answer=1)
        self.investigator.answered(self.question_3, self.household, answer="ANSWER")

        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_aggregates', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)

        self.client.login(username='Rajni', password='I_Rock')


    def test_downloaded_excel_file(self):
        file_name = "%s.csv" % self.batch.name
        response = self.client.post('/aggregates/spreadsheet_report', data={'batch': self.batch.pk})
        print response
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get('Content-Type'), "text/csv")
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="%s"' % file_name)

        row1 = ['Location', 'Household Head Name', 'IDENTIFIER_1', 'IDENTIFIER_2', '', 'IDENTIFIER_3']
        row2 = ['Kampala',  'Surname',             '1',            '1',            'OPTION 1', 'ANSWER']

        contents = "%s\r\n%s\r\n" % (",".join(row1), ",".join(row2))

        self.assertEquals(contents, response.content)

    def assert_restricted_permission_for(self, url):
        self.client.logout()

        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)

        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%url, status_code=302, target_status_code=200, msg_prefix='')

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

from datetime import date, datetime
from django.template.defaultfilters import slugify
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission

from django.contrib.contenttypes.models import ContentType
from rapidsms.contrib.locations.models import Location, LocationType
from survey.forms.filters import SurveyBatchFilterForm
from survey.models import GroupCondition, HouseholdMemberGroup, BatchQuestionOrder, UnknownDOBAttribute, EnumerationArea
from survey.models.batch import Batch
from survey.models.households import HouseholdHead, Household, HouseholdMember
from survey.models.backend import Backend
from survey.models.investigator import Investigator

from survey.models.question import Question, QuestionOption
from survey.models.surveys import Survey
from survey.tests.base_test import BaseTest


class ExcelDownloadTest(BaseTest):

    def setUp(self):
        self.client = Client()
        HouseholdMemberGroup.objects.create(name="GENERAL", order=2)
        self.member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)

        self.survey = Survey.objects.create(name='survey name', description='survey descrpition', type=False,
                                            sample_size=10)
        self.batch = Batch.objects.create(order = 1, name="BATCH A", survey=self.survey)
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

        BatchQuestionOrder.objects.create(question=self.question_1, batch=self.batch, order=1)
        BatchQuestionOrder.objects.create(question=self.question_2, batch=self.batch, order=2)
        BatchQuestionOrder.objects.create(question=self.question_3, batch=self.batch, order=3)

        location_type = LocationType.objects.create(name='Location', slug='location')
        kampala = Location.objects.create(name="Kampala", type=location_type)
        ea = EnumerationArea.objects.create(name="Kampala EA")
        ea.locations.add(kampala)

        backend = Backend.objects.create(name='something')
        self.investigator = Investigator.objects.create(name="investigator name", mobile_number="123", ea=ea,
                                                        backend=backend)
        self.household = Household.objects.create(investigator=self.investigator, uid=0, household_code='00010001',
                                                  ea=self.investigator.ea, survey=self.survey)
        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname", date_of_birth=date(2000, 9, 1))

        self.investigator.member_answered(self.question_1, self.household_head, answer=1, batch=self.batch)
        self.investigator.member_answered(self.question_2, self.household_head, answer=1, batch=self.batch)
        self.investigator.member_answered(self.question_3, self.household_head, answer="ANSWER", batch=self.batch)

        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_aggregates')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        self.client.login(username='Rajni', password='I_Rock')

    def test_downloaded_excel_file(self):
        file_name = "%s.csv" % self.batch.name
        data = {'batch': self.batch.pk, 'survey': self.batch.survey.pk}
        response = self.client.get('/aggregates/spreadsheet_report', data=data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.get('Content-Type'), "text/csv")
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="%s"' % file_name)
        household_id = self.household.household_code

        row1 = ['Location', 'Household ID', 'Name', 'Age', 'Month of Birth', 'Year of Birth', 'Gender', 'QUESTION_1', 'QUESTION_2', '', 'QUESTION_3']
        row2 = ['Kampala', household_id, 'Surname', '14', '9',  '2000',   'Male',      '1',       '1', 'OPTION 1',  'ANSWER']

        contents = "%s\r\n%s\r\n" % (",".join(row1), ",".join(row2))

        self.assertEquals(contents, response.content)

    def test_downloaded_excel_file_with_unknown_year_and_month_of_birth(self):
        file_name = "%s.csv" % self.batch.name
        member = HouseholdMember.objects.create(household=self.household, surname="someone", date_of_birth=date(2000, 9, 1))
        UnknownDOBAttribute.objects.create(household_member=member, type="YEAR")
        UnknownDOBAttribute.objects.create(household_member=member, type="MONTH")

        data = {'batch': self.batch.pk, 'survey': self.batch.survey.pk}
        response = self.client.get('/aggregates/spreadsheet_report', data=data)
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.get('Content-Type'), "text/csv")
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="%s"' % file_name)
        household_id = self.household.household_code

        row1 = ['Location', 'Household ID', 'Name', 'Age', 'Month of Birth', 'Year of Birth', 'Gender', 'QUESTION_1', 'QUESTION_2', '', 'QUESTION_3']
        row2 = ['Kampala', household_id, 'Surname', '14', '9',  '2000',   'Male',      '1',       '1', 'OPTION 1',  'ANSWER']
        row3 = ['Kampala', household_id, 'someone', '14', '99',  '99',   'Male', '', '', '']

        contents = "%s\r\n%s\r\n%s\r\n" % (",".join(row1), ",".join(row2), ",".join(row3))

        self.assertEquals(contents, response.content)
        
    def test_downloaded_excel_when_only_survey_supplied(self):
        batchB = Batch.objects.create(order=2, name="different batch", survey=self.survey)
        question_1B = Question.objects.create(group=self.member_group, text="Question 1 B", answer_type=Question.NUMBER,
                                                  order=1, identifier='Q1B')
        question_2B = Question.objects.create(group=self.member_group, text="Question 2B", answer_type=Question.MULTICHOICE,
                                                  order=2, identifier='Q2B')
        question_3B = Question.objects.create(group=self.member_group, text="Question 3B", answer_type=Question.NUMBER,
                                                  order=3, identifier='Q3B')

        yes_option = QuestionOption.objects.create(question=question_2B, text="Yes", order=1)
        no_option = QuestionOption.objects.create(question=question_2B, text="No", order=2)

        question_1B.batches.add(batchB)
        question_2B.batches.add(batchB)
        question_3B.batches.add(batchB)

        BatchQuestionOrder.objects.create(question=question_1B, batch=batchB, order=1)
        BatchQuestionOrder.objects.create(question=question_2B, batch=batchB, order=2)
        BatchQuestionOrder.objects.create(question=question_3B, batch=batchB, order=3)

        self.investigator.member_answered(question_1B, self.household_head, 1, batchB)
        self.investigator.member_answered(question_2B, self.household_head, no_option.order, batchB)
        self.investigator.member_answered(question_3B, self.household_head, 1, batchB)

        header_structure = ['Location', 'Household ID', 'Name', 'Age', 'Month of Birth', 'Year of Birth', 'Gender',
                            self.question_1.identifier, self.question_2.identifier, '', self.question_3.identifier,
                            question_1B.identifier, question_2B.identifier, '', question_3B.identifier]

        expected_csv_data = ['Kampala', self.household.household_code, 'Surname', '14', '9',  '2000',   'Male',
                             '1',       '1', 'OPTION 1',  'ANSWER', str(1), str(no_option.order), no_option.text, '1']

        contents = "%s\r\n%s\r\n" % (",".join(header_structure), ",".join(expected_csv_data))

        file_name = "%s.csv" % self.survey.name
        response = self.client.get('/aggregates/spreadsheet_report', data={'survey': self.survey.pk, 'batch':''})
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.get('Content-Type'), "text/csv")
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="%s"' % file_name)

        self.assertEquals(contents, response.content)

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/aggregates/spreadsheet_report')


class ExcelDownloadViewTest(BaseTest):

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
        Survey.objects.create(name="survey")

        response = self.client.get('/aggregates/download_spreadsheet')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/download_excel.html', templates)
        self.assertIsInstance(response.context['survey_batch_filter_form'], SurveyBatchFilterForm)

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/aggregates/download_spreadsheet')


class ReportForCompletedInvestigatorTest(BaseTest):
    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        self.survey = Survey.objects.create(name='some group')
        self.batch = Batch.objects.create(name='BatchA', survey=self.survey)
        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_aggregates', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)

        self.client.login(username='Rajni', password='I_Rock')

    def test_should_have_header_fields_in_download_report(self):
        survey = Survey.objects.create(name='some survey')
        file_name = "investigator.csv"
        response = self.client.post('/investigators/completed/download/', {'survey': survey.id})
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.get('Content-Type'), "text/csv")
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="%s"' % file_name)
        row1 = ['Investigator', 'Phone Number']
        row1.extend(list(LocationType.objects.all().values_list('name', flat=True)))
        contents = "%s\r\n" % (",".join(row1))
        self.assertEquals(contents, response.content)

    def test_should_have_investigators_who_completed_a_selected_batch(self):
        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        city = LocationType.objects.create(name="City", slug=slugify("city"))
        uganda = Location.objects.create(name="Uganda", type=country)
        abim = Location.objects.create(name="Abim", type=district, tree_parent=uganda)
        kampala = Location.objects.create(name="Kampala", type=city, tree_parent=abim)
        ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
        ea.locations.add(kampala)


        backend = Backend.objects.create(name='something')
        survey = Survey.objects.create(name='SurveyA')
        batch = Batch.objects.create(name='Batch A')

        investigator_1 = Investigator.objects.create(name="investigator name_1", mobile_number="9876543210",
                                                     ea=ea, backend=backend)
        investigator_2 = Investigator.objects.create(name="investigator AYOYO", mobile_number="987654210",
                                                     ea=ea, backend=backend)

        household_1 = Household.objects.create(investigator=investigator_1, ea=investigator_1.ea, survey=survey)
        household_2 = Household.objects.create(investigator=investigator_2, ea=investigator_1.ea, survey=survey)

        member_group = HouseholdMemberGroup.objects.create(name='group1', order=1)
        question_1 = Question.objects.create(text="some question", answer_type=Question.NUMBER, order=1,
                                             group=member_group)
        batch.questions.add(question_1)

        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)

        member_1 = HouseholdMember.objects.create(household=household_1, date_of_birth=datetime(2000, 02, 02))
        member_2 = HouseholdMember.objects.create(household=household_1, date_of_birth=datetime(2000, 02, 02))
        HouseholdMember.objects.create(household=household_2, date_of_birth=datetime(2000, 02, 02))

        investigator_1.member_answered(question_1, member_1, 1, batch)
        investigator_1.member_answered(question_1, member_2, 1, batch)

        expected_data = [investigator_1.name, investigator_1.mobile_number]
        unexpected_data = [investigator_2.name, investigator_2.mobile_number]

        post_data = {'survey': survey.id, 'batch': batch.id}
        response = self.client.post('/investigators/completed/download/', post_data)
        row1 = ['Investigator', 'Phone Number']
        row1.extend(list(LocationType.objects.all().values_list('name', flat=True)))
        contents = "%s\r\n" % (",".join(row1))
        self.assertIn(contents, response.content)
        [self.assertIn(investigator_details, response.content) for investigator_details in expected_data]
        [self.assertNotIn(investigator_details, response.content) for investigator_details in unexpected_data]

    def test_restricted_permission(self):
        self.assert_login_required('/investigators/completed/download/')
        self.assert_restricted_permission_for('/investigators/completed/download/')
        self.assert_restricted_permission_for('/investigator_report/')

    def test_should_get_view_for_download(self):
        response = self.client.get('/investigator_report/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/download_investigator.html', templates)
        self.assertEquals(len(response.context['surveys']), 1)
        self.assertEquals(len(response.context['batches']), 1)
        self.assertIn(self.batch, response.context['batches'])
        self.assertIn(self.survey, response.context['surveys'])
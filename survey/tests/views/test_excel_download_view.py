from datetime import date, datetime
import django_rq
from model_mommy import mommy
from django.template.defaultfilters import slugify
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.http.request import QueryDict, MultiValueDict
from django.core.urlresolvers import reverse
from survey.forms.filters import SurveyBatchFilterForm
from survey.forms.logic import LogicForm
from survey.models import *
from survey.services.export_questions import *
from survey.tests.base_test import BaseTest
from survey.tests.models.survey_base_test import SurveyBaseTest


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


class ExportQuestionServiceExtra(SurveyBaseTest):
    # 10, 13-15, 18-27, 30-34, 50-62, 80-94

    def test__get_questions(self):
        self._create_ussd_non_group_questions()
        question = mommy.make(Question, qset=self.qset1)
        e_service = ExportQuestionsService(batch=self.qset)
        self.assertEquals(len(e_service.questions), self.qset.questions.count())
        e_service = ExportQuestionsService()
        self.assertTrue(len(e_service.questions) > self.qset.questions.count())

    def test_format_questions(self):
        self._create_ussd_group_questions()
        e_service = ExportQuestionsService(batch=self.qset)
        content = e_service.formatted_responses()
        self.assertIn(e_service.HEADERS, content)
        for idx, question in enumerate(self.qset.flow_questions):
            if question.group:
                self.assertIn(question.text, content[idx+1])

    def test_get_batch_question_as_dump(self):
        self._create_ussd_group_questions()
        numeric_question = Question.objects.filter(answer_type=NumericalAnswer.choice_name()).first()
        last_question = Question.objects.last()
        test_condition = 'equals'
        test_param = '15'
        form_data = {
            'action': LogicForm.SKIP_TO,
            'next_question': last_question.id,
            'condition': test_condition,
            'value': test_param
        }
        logic_form = LogicForm(numeric_question, data=form_data)
        self.assertTrue(logic_form.is_valid())
        logic_form.save()
        content = get_batch_question_as_dump(self.qset.flow_questions)
        for idx, question in enumerate(self.qset.flow_questions):
            self.assertIn(question.identifier, content[idx+1])

    def test_get_question_as_dump(self):
        self._create_ussd_non_group_questions()
        content = get_batch_question_as_dump(self.qset.flow_questions)
        for idx, question in enumerate(self.qset.flow_questions):
            self.assertIn(question.identifier, content[idx+1])


class DownloadExcelExtra(SurveyBaseTest):

    def setUp(self):
        super(DownloadExcelExtra, self).setUp()
        self.client = Client()
        User.objects.create_user(username='useless', email='demo3@kant.com', password='I_Suck')
        user = User.objects.create_user('demo13', 'demo3@kant.com', 'demo13')
        self.assign_permission_to(user, 'can_view_aggregates')
        self.assign_permission_to(user, 'can_view_users')
        self.client.login(username='demo13', password='demo13')

    def test_email_excel(self):
        self._create_ussd_non_group_questions(self.qset)
        answers = []
        n_quest = Question.objects.get(answer_type=NumericalAnswer.choice_name())
        t_quest = Question.objects.get(answer_type=TextAnswer.choice_name())
        m_quest = Question.objects.get(answer_type=MultiChoiceAnswer.choice_name())
        # first is numeric, then text, then multichioice
        answers = [{n_quest.id: 1, t_quest.id: 'Hey Man', m_quest.id: 'Y'},
                   {n_quest.id: 5, t_quest.id: 'Hey Boy', m_quest.id: 'Y'},
                   {n_quest.id: 15, t_quest.id: 'Hey Girl!', m_quest.id: 'N'},
                   {n_quest.id: 15, t_quest.id: 'Hey Part!'}
                   ]
        question_map = {n_quest.id: n_quest, t_quest.id: t_quest, m_quest.id: m_quest}
        interview = self.interview
        Interview.save_answers(self.qset, self.survey, self.ea,
                               self.access_channel, question_map, answers)
        # confirm that 11 answers has been created
        self.assertEquals(NumericalAnswer.objects.count(), 4)
        self.assertEquals(TextAnswer.objects.count(), 4)
        self.assertEquals(MultiChoiceAnswer.objects.count(), 3)
        self.assertEquals(TextAnswer.objects.first().to_text().lower(), 'Hey Man'.lower())
        self.assertEquals(MultiChoiceAnswer.objects.first().as_text.lower(), 'Y'.lower())
        self.assertEquals(MultiChoiceAnswer.objects.first().as_value, str(QuestionOption.objects.get(text='Y').order))
        url = reverse('excel_report')
        data = {'survey': self.survey.id, 'batch': self.qset.id, 'multi_option': SurveyBatchFilterForm.AS_TEXT,
                'action': 'Email Spreadsheet'}
        response = self.client.get(url, follow=True, data=data)
        self.assertTrue(response.context['a_form'].is_valid())
        self.assertIn('Email would be sent to', response.content)
        # not test the zip download
        data = {'survey': self.survey.id, 'batch': self.qset.id, 'multi_option': SurveyBatchFilterForm.AS_TEXT,
                'action': 'Download'}       # really anything would do
        response = self.client.get(url, follow=True, data=data)
        self.assertEquals(response['content-type'], 'application/zip')
        self.assertIn('%s.zip' % self.qset.name, response['content-disposition'])

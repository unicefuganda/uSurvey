from django.test import TestCase
from django.test.client import Client
from xlrd import open_workbook
from survey.models import *

class ExcelDownloadTest(TestCase):

    def setUp(self):
        self.client = Client()
        survey = Survey.objects.create(name='Survey Name', description='Survey description')
        self.batch = Batch.objects.create(survey=survey, order = 1, name="BATCH A")
        indicator = Indicator.objects.create(batch=self.batch, order=1, identifier="IDENTIFIER")
        self.question_1 = Question.objects.create(indicator=indicator, text="How many members are there in this household?", answer_type=Question.NUMBER, order=1)
        self.question_2 = Question.objects.create(indicator=indicator, text="How many members are there in this household?", answer_type=Question.MULTICHOICE, order=2)
        self.option_1_1 = QuestionOption.objects.create(question=self.question_2, text="OPTION 1", order=1)
        self.option_1_2 = QuestionOption.objects.create(question=self.question_2, text="OPTION 2", order=2)
        self.question_3 = Question.objects.create(indicator=indicator, text="How many of them are male?", answer_type=Question.TEXT, order=3)
        self.investigator = Investigator.objects.create(name="investigator name", mobile_number="123", location=Location.objects.create(name="Kampala"))
        self.household = Household.objects.create(investigator=self.investigator)
        self.household_head = HouseholdHead.objects.create(household=self.household, surname="Surname")

        self.investigator.answered(self.question_1, self.household, answer=1)
        self.investigator.answered(self.question_2, self.household, answer=1)
        self.investigator.answered(self.question_3, self.household, answer="ANSWER")

    def test_downloaded_excel_file(self):
        file_name = "%s.csv" % self.batch.name
        response = self.client.post('/aggregates/excel_report', data={'batch': self.batch.pk})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get('Content-Type'), "text/csv")
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="%s"' % file_name)

        row1 = ['Location', 'Household Head Name', 'IDENTIFIER_1', 'IDENTIFIER_2', '', 'IDENTIFIER_3']
        row2 = ['Kampala',  'Surname',             '1',            '1',            'OPTION 1', 'ANSWER']

        contents = "%s\r\n%s\r\n" % (",".join(row1), ",".join(row2))

        self.assertEquals(contents, response.content)

class ExcelDownloadViewTest(TestCase):

    def test_get(self):
        client = Client()
        response = self.client.get('/aggregates/download_excel')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/download_excel.html', templates)
        self.assertEquals(len(response.context['batches']), 0)
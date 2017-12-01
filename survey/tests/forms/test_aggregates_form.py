import string
from model_mommy import mommy
from django.test import TestCase
from survey.tests.base_test import BaseTest
from survey.models import Survey, Batch
from survey.forms.aggregates import InterviewerReportForm


class TestAggregatorForm(BaseTest):

    def setUp(self):
        self.survey = mommy.make(Survey, name='testsurvey')
        self.batch = mommy.make(Batch, survey=self.survey)
        self.batch2 = mommy.make(Batch, survey=self.survey)
        self.batch3 = mommy.make(Batch, survey=self.survey)

    def test_aggregator_form_works_correctly(self):
        data = {'survey': self.survey.id}
        survey = mommy.make(Survey, name='testsurvey2')
        form = InterviewerReportForm()
        self.assertEquals(form.fields['survey'].queryset.count(), Survey.objects.count())
        form = InterviewerReportForm(data=data)
        self.assertEquals(form.is_valid(), True)
        self.assertEquals(form.fields['survey'].queryset.count(), 2)
        self.assertEquals(form.fields['batch'].queryset.count(), self.survey.batches.count())


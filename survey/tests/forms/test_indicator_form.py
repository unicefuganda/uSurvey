from django.test import TestCase
from survey.forms.indicator import IndicatorForm
from survey.models import QuestionModule, Batch, Survey


class IndicatorFormTest(TestCase):

    def setUp(self):
        module = QuestionModule.objects.create(name="Health")
        self.survey = Survey.objects.create(name="Health survey")
        batch = Batch.objects.create(name="Health", survey=self.survey)

        self.form_data = {'module': module.id,
                          'name': 'Health',
                          'description': 'some description',
                          'measure': '%',
                          'batch': batch.id,
                          'survey': self.survey.id, }

    def test_valid(self):
        indicator_form = IndicatorForm(self.form_data)
        self.assertTrue(indicator_form.is_valid())

    def test_invalid(self):
        form_data = self.form_data.copy()
        form_data['module'] = ''
        indicator_form = IndicatorForm(form_data)
        self.assertFalse(indicator_form.is_valid())
        self.assertEqual(['This field is required.'],
                         indicator_form.errors['module'])

    def test_batch_should_belong_to_survey(self):
        form_data = self.form_data.copy()
        new_survey = Survey.objects.create(name="haha")
        new_batch = Batch.objects.create(
            name="batch not belonging to survey", survey=new_survey)
        form_data['batch'] = new_batch.id
        indicator_form = IndicatorForm(form_data)
        self.assertFalse(indicator_form.is_valid())
        self.assertEqual(
            ["Select a valid choice. That choice is not one of the available choices."], indicator_form.errors['batch'])

    def test_survey_should_not_be_empty(self):
        form_data = self.form_data.copy()
        form_data['survey'] = ''
        indicator_form = IndicatorForm(form_data)
        self.assertFalse(indicator_form.is_valid())
        self.assertEqual(['This field is required.'],
                         indicator_form.errors['survey'])

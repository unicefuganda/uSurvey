from django.test import TestCase
from survey.models.locations import *
from survey.forms.filters import IndicatorFilterForm
from survey.forms.filters import QuestionFilterForm
from survey.forms.filters import SurveyBatchFilterForm
from survey.models import Batch
from survey.models import EnumerationArea
from survey.models import QuestionModule
from survey.models import Survey


class QuestionFilterFormTest(TestCase):

    def test_form_instance_should_have_all_modules(self):
        module_1 = QuestionModule.objects.create(
            name="Module 1", description="Test1")
        module_2 = QuestionModule.objects.create(
            name="Module 2", description="Test12")
        module_3 = QuestionModule.objects.create(
            name="Module 2", description="Test13")
        question_filter_form = QuestionFilterForm()
        self.assertIn((module_1.id, module_1.name),
                      question_filter_form.fields['modules'].choices)
        self.assertIn((module_2.id, module_2.name),
                      question_filter_form.fields['modules'].choices)
        self.assertIn((module_3.id, module_3.name),
                      question_filter_form.fields['modules'].choices)

    def test_form_instance_should_have_all_question_types(self):
        question_filter_form = QuestionFilterForm()
        all_question_types = [('Numerical Answer', 'Numerical Answer'), (
            'Text Answer', 'Text Answer'), ('Multi Choice Answer', 'Multi Choice Answer')]
        [self.assertIn(question_type, question_filter_form.fields[
                       'question_types'].choices) for question_type in all_question_types]

class IndicatorFilterFormTest(TestCase):
    
    def setUp(self):
        self.module_1 = QuestionModule.objects.create(name="Module 1")
        self.module_2 = QuestionModule.objects.create(name="Module 2")
        self.module_3 = QuestionModule.objects.create(name="Module 3")
        self.survey = Survey.objects.create(name="Survey A")
        self.survey_2 = Survey.objects.create(name="Survey B")
        self.batch = Batch.objects.create(name="Batch A", survey=self.survey)
        self.batch_1 = Batch.objects.create(name="Batch B", survey=self.survey)
        self.batch_3 = Batch.objects.create(
            name="Batch C", survey=self.survey_2)
        self.batch_4 = Batch.objects.create(
            name="Batch D", survey=self.survey_2)

    def test_form_instance_should_have_all_batches(self):
        indicator_filter_form = IndicatorFilterForm()
        self.assertEqual(5, len(indicator_filter_form.fields['batch'].choices))
        self.assertIn((self.batch_1.id, self.batch_1.name),
                      indicator_filter_form.fields['batch'].choices)
        self.assertIn((self.batch.id, self.batch.name),
                      indicator_filter_form.fields['batch'].choices)
        self.assertIn((self.batch_3.id, self.batch_3.name),
                      indicator_filter_form.fields['batch'].choices)
        self.assertIn((self.batch_4.id, self.batch_4.name),
                      indicator_filter_form.fields['batch'].choices)

    def test_form_instance_should_have_all_surveys(self):
        indicator_filter_form = IndicatorFilterForm()
        self.assertEqual(
            3, len(indicator_filter_form.fields['survey'].choices))
        self.assertIn((self.survey.id, self.survey.name),
                      indicator_filter_form.fields['survey'].choices)
        self.assertIn((self.survey_2.id, self.survey_2.name),
                      indicator_filter_form.fields['survey'].choices)

    def test_form_should_show_batches_under_a_survey_only_if_survey_given(self):
        indicator_filter_form = IndicatorFilterForm(
            data={'survey': str(self.survey.id), 'batch': 'All'})
        self.assertEqual(3, len(indicator_filter_form.fields['batch'].choices))
        self.assertIn((self.batch_1.id, self.batch_1.name),
                      indicator_filter_form.fields['batch'].choices)
        self.assertIn((self.batch.id, self.batch.name),
                      indicator_filter_form.fields['batch'].choices)

    def test_invalid_survey_choices(self):
        indicator_filter_form = IndicatorFilterForm(
            data={'survey': 'ayoyoyoyoooo', 'batch': str(self.batch.id)})
        self.assertFalse(indicator_filter_form.is_valid())
        self.assertEqual(['Select a valid choice. ayoyoyoyoooo is not one of the available choices.'],
                         indicator_filter_form.errors['survey'])

    def test_invalid_batch_choices(self):
        indicator_filter_form = IndicatorFilterForm(
            data={'survey': str(self.survey.id), 'batch': 'ayoyoyooooooo'})
        self.assertTrue(indicator_filter_form.is_valid())
        self.assertEqual(['Select a valid choice. ayoyoyooooooo is not one of the available choices.'],
                         indicator_filter_form.errors['batch'])

    def test_only_survey_batches_are_allowed(self):
        bacth_id_not_belongin_got_self_survey = str(self.batch_3.id)
        data = {'survey': str(self.survey.id),
                'batch': bacth_id_not_belongin_got_self_survey}
        indicator_filter_form = IndicatorFilterForm(data=data)
        self.assertTrue(indicator_filter_form.is_valid())
        self.assertEqual(['Select a valid choice. %s is not one of the available choices.' % data[
                         'batch']], indicator_filter_form.errors['batch'])

    def test_form_instance_should_have_all_modules(self):
        indicator_filter_form = IndicatorFilterForm()
        self.assertEqual(
            4, len(indicator_filter_form.fields['module'].choices))
        self.assertIn((self.module_1.id, self.module_1.name),
                      indicator_filter_form.fields['module'].choices)
        self.assertIn((self.module_2.id, self.module_2.name),
                      indicator_filter_form.fields['module'].choices)
        self.assertIn((self.module_3.id, self.module_3.name),
                      indicator_filter_form.fields['module'].choices)

class CompletionLocationFilterFormTest(TestCase):

    def setUp(self):
        self.survey = Survey.objects.create(name="Survey A")
        self.survey_2 = Survey.objects.create(name="Survey B")
        self.batch = Batch.objects.create(name="Batch A", survey=self.survey)
        self.batch_1 = Batch.objects.create(
            name="Batch B", survey=self.survey_2)
        self.country = LocationType.objects.create(
            name="country", slug="country")
        self.district = LocationType.objects.create(
            name="district", parent=self.country, slug="district")
        self.location = Location.objects.create(
            name="Uganda", type=self.country)
        self.another_location = Location.objects.create(
            name="Kampala", parent=self.location, type=self.district)
        self.ea = EnumerationArea.objects.create(name="EA")
        self.ea.locations.add(self.another_location)
        self.data = {'survey': self.survey.id,
                     'batch': self.batch.id,
                     'location': self.another_location.id,
                     'ea': self.ea.id}

class SurveyBatchFilterFormTest(TestCase):

    def setUp(self):
        self.survey = Survey.objects.create(name="Survey A")
        self.survey_2 = Survey.objects.create(name="Survey B")
        self.batch = Batch.objects.create(name="Batch A", survey=self.survey)
        self.batch_1 = Batch.objects.create(
            name="Batch B", survey=self.survey_2)
        self.data = {'survey': self.survey.id,
                     'batch': self.batch.id,
                     'multi_option': 1}

    def test_valid(self):
        survey_batch_filter_form = SurveyBatchFilterForm(self.data)
        self.assertTrue(survey_batch_filter_form.is_valid())

    def test_empty_batch_is_valid(self):
        data = self.data.copy()
        data['batch'] = ''
        survey_batch_filter_form = SurveyBatchFilterForm(data)
        self.assertTrue(survey_batch_filter_form.is_valid())

    def assert_invalid_if_field_does_not_exist(self, field_key):
        form_data = self.data.copy()
        non_existing_survey_id = 666
        form_data[field_key] = non_existing_survey_id
        survey_batch_filter_form = SurveyBatchFilterForm(form_data)
        self.assertFalse(survey_batch_filter_form.is_valid())
        message = "Select a valid choice. That choice is not one of the available choices."
        self.assertEqual([message], survey_batch_filter_form.errors[field_key])

    def assert_invalid_if_field_is_non_sense(self, field_key):
        form_data = self.data.copy()
        form_data[field_key] = 'non_sense_hohoho_&^%$#'
        survey_batch_filter_form = SurveyBatchFilterForm(form_data)
        self.assertFalse(survey_batch_filter_form.is_valid())
        message = "Select a valid choice. That choice is not one of the available choices."
        self.assertEqual([message], survey_batch_filter_form.errors[field_key])

    def test_invalid_if_batch_is_not_under_survey(self):
        form_data = self.data.copy()
        form_data['survey'] = self.survey.id
        form_data['batch'] = self.batch_1.id
        survey_batch_filter_form = SurveyBatchFilterForm(form_data)
        self.assertFalse(survey_batch_filter_form.is_valid())
        message = "Select a valid choice. That choice is not one of the available choices."
        self.assertEqual([message], survey_batch_filter_form.errors['batch'])

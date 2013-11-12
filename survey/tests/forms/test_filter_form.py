from django.test import TestCase
from survey.forms.filters import QuestionFilterForm, IndicatorFilterForm
from survey.models import Question, QuestionModule, HouseholdMemberGroup, Indicator, Batch, Survey


class QuestionFilterFormTest(TestCase):

    def test_form_instance_should_have_all_modules(self):
        module_1 = QuestionModule.objects.create(name="Module 1")
        module_2 = QuestionModule.objects.create(name="Module 2")
        module_3 = QuestionModule.objects.create(name="Module 2")

        question_filter_form = QuestionFilterForm()

        self.assertIn((module_1.id, module_1.name), question_filter_form.fields['modules'].choices)
        self.assertIn((module_2.id, module_2.name), question_filter_form.fields['modules'].choices)
        self.assertIn((module_3.id, module_3.name), question_filter_form.fields['modules'].choices)

    def test_form_instance_should_have_all_groups(self):
        group_1 = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
        group_2 = HouseholdMemberGroup.objects.create(name="Group 2", order=2)
        group_3 = HouseholdMemberGroup.objects.create(name="Group 3", order=3)

        question_filter_form = QuestionFilterForm()

        all_groups = [group_1, group_2, group_3]

        [self.assertIn((group.id, group.name), question_filter_form.fields['groups'].choices) for group in all_groups]

    def test_form_instance_should_have_all_question_types(self):

        question_filter_form = QuestionFilterForm()

        all_question_types = [('number', 'Number'), ('text', 'Text'), ('multichoice', 'Multichoice')]

        [self.assertIn(question_type, question_filter_form.fields['question_types'].choices) for question_type in all_question_types]


class IndicatorFilterFormTest(TestCase):

    def setUp(self):
        self.module_1 = QuestionModule.objects.create(name="Module 1")
        self.module_2 = QuestionModule.objects.create(name="Module 2")
        self.module_3 = QuestionModule.objects.create(name="Module 3")
        self.survey = Survey.objects.create(name="Survey A")
        self.survey_2 = Survey.objects.create(name="Survey B")
        self.batch = Batch.objects.create(name="Batch A", survey = self.survey)
        self.batch_1 = Batch.objects.create(name="Batch B", survey = self.survey)
        self.batch_3 = Batch.objects.create(name="Batch C", survey = self.survey_2)
        self.batch_4 = Batch.objects.create(name="Batch D", survey = self.survey_2)

    def test_form_instance_should_have_all_batches(self):
        indicator_filter_form = IndicatorFilterForm()

        self.assertEqual(5, len(indicator_filter_form.fields['batch'].choices))
        self.assertIn((self.batch_1.id, self.batch_1.name), indicator_filter_form.fields['batch'].choices)
        self.assertIn((self.batch.id, self.batch.name), indicator_filter_form.fields['batch'].choices)
        self.assertIn((self.batch_3.id, self.batch_3.name), indicator_filter_form.fields['batch'].choices)
        self.assertIn((self.batch_4.id, self.batch_4.name), indicator_filter_form.fields['batch'].choices)

    def test_form_instance_should_have_all_surveys(self):
        indicator_filter_form = IndicatorFilterForm()

        self.assertEqual(3, len(indicator_filter_form.fields['survey'].choices))
        self.assertIn((self.survey.id, self.survey.name), indicator_filter_form.fields['survey'].choices)
        self.assertIn((self.survey_2.id, self.survey_2.name), indicator_filter_form.fields['survey'].choices)

    def test_form_should_show_batches_under_a_survey_only_if_survey_given(self):
        indicator_filter_form = IndicatorFilterForm(data={'survey':str(self.survey.id), 'batch':'All'})

        self.assertEqual(3, len(indicator_filter_form.fields['batch'].choices))
        self.assertIn((self.batch_1.id, self.batch_1.name), indicator_filter_form.fields['batch'].choices)
        self.assertIn((self.batch.id, self.batch.name), indicator_filter_form.fields['batch'].choices)

    def test_invalid_survey_choices(self):
        indicator_filter_form = IndicatorFilterForm(data={'survey':'ayoyoyoyoooo', 'batch':str(self.batch.id)})

        self.assertFalse(indicator_filter_form.is_valid())
        self.assertEqual(['Select a valid choice. ayoyoyoyoooo is not one of the available choices.'],indicator_filter_form.errors['survey'])

    def test_invalid_batch_choices(self):
        indicator_filter_form = IndicatorFilterForm(data={'survey':str(self.survey.id), 'batch':'ayoyoyooooooo'})

        self.assertFalse(indicator_filter_form.is_valid())
        self.assertEqual(['Select a valid choice. ayoyoyooooooo is not one of the available choices.'],indicator_filter_form.errors['batch'])

    def test_only_survey_batches_are_allowed(self):
        bacth_id_not_belongin_got_self_survey = str(self.batch_3.id)
        data = {'survey':str(self.survey.id), 'batch':bacth_id_not_belongin_got_self_survey}
        indicator_filter_form = IndicatorFilterForm(data=data)

        self.assertFalse(indicator_filter_form.is_valid())
        self.assertEqual(['Select a valid choice. %s is not one of the available choices.'%data['batch']],indicator_filter_form.errors['batch'])

    def test_form_instance_should_have_all_modules(self):
        indicator_filter_form = IndicatorFilterForm()

        self.assertEqual(4, len(indicator_filter_form.fields['module'].choices))
        self.assertIn((self.module_1.id, self.module_1.name), indicator_filter_form.fields['module'].choices)
        self.assertIn((self.module_2.id, self.module_2.name), indicator_filter_form.fields['module'].choices)
        self.assertIn((self.module_3.id, self.module_3.name), indicator_filter_form.fields['module'].choices)
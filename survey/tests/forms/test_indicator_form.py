from model_mommy import mommy
from django.http import QueryDict
from django.test import TestCase
from survey.forms.indicator import IndicatorForm, IndicatorVariableForm
from survey.models import *


class IndicatorFormTest(TestCase):

    def setUp(self):
        self.survey = Survey.objects.create(name="Health survey")
        # self.batch = Batch.objects.create(name="Health", survey=self.survey)
        self.qset = QuestionSet.objects.create(name="qset", description="blahblah")
        self.form_data = {
                          'name': 'Health',
                          'description': 'some description',
                          'question_set': self.qset,
                          'survey': self.survey.id
                          }

    def test_invalid(self):
        form_data = self.form_data
        form_data['name'] = ''
        indicator_form = IndicatorForm(form_data)
        self.assertFalse(indicator_form.is_valid())
        self.assertEqual(['This field is required.'],
                         indicator_form.errors['name'])

    def test_survey_does_not_match_qset(self):
        qset = mommy.make(Batch, survey=self.survey)
        form_data = self.form_data
        indicator_form = IndicatorForm(data=form_data)
        self.assertFalse(indicator_form.is_valid())
        self.assertIn('question_set', indicator_form.errors)

    def test_batch_should_belong_to_survey(self):
        form_data = self.form_data.copy()
        new_survey = Survey.objects.create(name="haha")
        new_batch = Batch.objects.create(
            name="batch not belonging to survey", survey=new_survey)
        form_data['batch'] = new_batch.id
        indicator_form = IndicatorForm(form_data)
        self.assertFalse(indicator_form.is_valid())
        # self.assertEqual(
        #     ["Select a valid choice. That choice is not one of the available choices."], indicator_form.errors['batch'])

    def test_survey_should_not_be_empty(self):
        form_data = self.form_data.copy()
        form_data['survey'] = ''
        indicator_form = IndicatorForm(form_data)
        self.assertFalse(indicator_form.is_valid())
        self.assertEqual(['This field is required.'],
                         indicator_form.errors['survey'])

    def test_indicator_formulae(self):
        qset = mommy.make(Batch, survey=self.survey)
        indicator_variable = mommy.make(IndicatorVariable, name='test_variable')
        indicator_variable2 = mommy.make(IndicatorVariable, name='test_variable2')
        form_data = self.form_data
        form_data['formulae'] = '{{*-a}} > 1'
        form_data['question_set'] = qset.id
        data = QueryDict(mutable=True, query_string='variables[]=%s&variables[]=%s' % (indicator_variable.id,
                                                                                       indicator_variable2.id))
        data.update(**form_data)
        indicator_form = IndicatorForm(data)
        self.assertFalse(indicator_form.is_valid())
        form_data['formulae'] = '{{test_variable > 1'
        data.update(**form_data)
        indicator_form = IndicatorForm(data)
        self.assertFalse(indicator_form.is_valid())
        form_data['formulae'] = '{{test_variable}} > 1'
        data.update(**form_data)
        indicator_form = IndicatorForm(data)
        self.assertTrue(indicator_form.is_valid())

    def test_variable_formula_form(self):
        qset = mommy.make(Batch, survey=self.survey)
        question = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        qset.start_question = question
        qset.save()
        indicator_variable = mommy.make(IndicatorVariable, name='test_variable')
        indicator_variable2 = mommy.make(IndicatorVariable, name='test_variable2')
        indicator = mommy.make(Indicator, question_set=qset, survey=self.survey)
        data = {'name': 'variable1', 'test_question': question.id, 'validation_test': 'between',
                'description': 'test desc'}
        form = IndicatorVariableForm(indicator, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('min', form.errors['__all__'][0])
        self.assertIn('max', form.errors['__all__'][0])


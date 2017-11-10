from model_mommy import mommy
import json
from django.contrib.auth.models import User
from django.test.utils import setup_test_environment
from django.test import Client
from django.core.urlresolvers import reverse
from survey.forms.indicator import IndicatorForm, IndicatorFormulaeForm, IndicatorVariableForm
from survey.forms.filters import IndicatorFilterForm
from survey.models import (QuestionModule, Batch, Indicator, Survey, Question, QuestionSet, Interview,
                           IndicatorVariableCriteria, IndicatorVariable, NumericalAnswer, TextAnswer,
                           MultiChoiceAnswer, QuestionOption, ListingTemplate, Location, LocationType)
from survey.tests.base_test import BaseTest
from survey.tests.models.survey_base_test import SurveyBaseTest


class IndicatorViewTest(SurveyBaseTest):

    def setUp(self):
        setup_test_environment()
        super(IndicatorViewTest, self).setUp()
        self.variable1 = mommy.make(IndicatorVariable)
        self.indicator_criteria = mommy.make(IndicatorVariableCriteria)
        self.form_data = {
                          'name': 'Health',
                          'description': 'some description',
                          'question_set': self.qset.id,
                          'survey': self.survey.id}
        self.variable_data = {
            'name': 'test_variable',
            'validation_test': 'between',
            'description': 'test indicator variable',
            'var_qset': self.qset.id,
            'min': '1',
            'max': '10'
        }
        User.objects.create_user(
            username='useless', email='demo4@kant.com', password='I_Suck')
        self.raj = self.assign_permission_to(User.objects.create_user('demo4', 'demo4@kant.com', 'demo4'),
                                             'can_view_batches')
        self.assign_permission_to(self.raj, 'can_view_investigators')
        self.assign_permission_to(self.raj, 'can_view_household_groups')
        self.client.login(username='demo4', password='demo4')

    def _test_create_indicator(self):
        self._test_create_indicator_variable()
        data = self.form_data.copy()
        data['variables'] = list(IndicatorVariable.objects.values_list('id', flat=True))
        data['formulae'] = '{{%s}}/{{%s}}' % tuple(list(IndicatorVariable.objects.values_list('name', flat=True)))
        count = Indicator.objects.count()
        response = self.client.post(reverse('new_indicator_page'), data=data)
        self.assertRedirects(response, reverse('list_indicator_page'))
        self.assertTrue(count+1, Indicator.objects.count())
        indicator = Indicator.objects.last()
        return indicator, data

    def _test_create_indicator_variable(self, **kwargs):
        self._create_ussd_non_group_questions()
        data = self.variable_data.copy()
        data.update(kwargs)
        numeric_question = Question.objects.filter(answer_type=NumericalAnswer.choice_name(),
                                                   qset__id=self.qset.id).first()
        data['test_question'] = numeric_question.id
        url = reverse('add_variable')
        response = self.client.get(url)
        self.assertTrue(response.status_code, 200)
        self.assertIn('indicator/indicator_variable.html', [t.name for t in response.templates])
        IndicatorVariable.objects.all().delete()
        variable_count = IndicatorVariable.objects.count()
        # now post to create
        response = self.client.post(url, data=data)
        self.assertIn(response.status_code, [200, 302])
        self.assertEquals(IndicatorVariable.objects.count(), variable_count+1)
        data['name'] = 'variable2'
        data['max'] = '1000'
        data['min'] = '0'
        variable_count = IndicatorVariable.objects.count()
        response = self.client.post(url, data=data)
        self.assertIn(response.status_code, [200, 302])
        self.assertEquals(IndicatorVariable.objects.count(), variable_count + 1)

    def test_create_variable_from_existing_indicator(self):
        indicator, data = self._test_create_indicator()
        text_question = Question.objects.filter(answer_type=TextAnswer.choice_name(),
                                                qset__id=self.qset.id).first()
        data = self.variable_data.copy()
        data['test_question'] = text_question.id
        data['name'] = 'varaiabe_again'
        data['contains'] = 'tee boy'
        url = reverse('add_indicator_variable', args=(indicator.id, ))
        response = self.client.post(url, data=data)
        self.assertIn(response.status_code, [200, 302])
        self.assertEquals(IndicatorVariable.objects.filter(name=data['name']).count(), 1)

    def test_get_new_indicator(self):
        response = self.client.get(reverse('new_indicator_page'))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('indicator/new.html', templates)
        self.assertIsNotNone(response.context['indicator_form'])
        self.assertIsInstance(response.context['indicator_form'], IndicatorForm)
        self.assertIn(response.context['title'], "Add Indicator")
        self.assertIn(response.context['button_label'], "Create")
        self.assertIn(response.context['action'], reverse('new_indicator_page'))

    def test_post_indicator_with_incomplete_params_does_not_create(self):
        data = self.form_data.copy()
        del data['survey']
        self.failIf(Indicator.objects.filter(**data))
        another_survey = Survey.objects.create(name="Education survey")
        response = self.client.post(reverse('new_indicator_page'), data=data)
        error_message = "Question set %s does not belong to the selected Survey." % self.qset.name
        self.assertIn(error_message, response.content)

    def test_post_indicator_with_incorrect_question_set_does_not_create(self):
        data = self.form_data.copy()
        self.failIf(Indicator.objects.filter(**data))
        another_survey = Survey.objects.create(name="Education survey")
        data['survey'] = another_survey.id
        response = self.client.post(reverse('new_indicator_page'), data=data)
        error_message = "Indicator was not created."
        self.assertIn(error_message, response.content)

    def test_edit_indicator_variable(self):
        self._test_create_indicator_variable()
        variable = IndicatorVariable.objects.first()
        url = reverse('edit_indicator_variable', args=(variable.id, ))
        data = self.variable_data.copy()
        data['name'] = 'edited_variable_name_13'
        response = self.client.post(url, data=data)
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(IndicatorVariable.objects.filter(name=data['name']).exists())
        # now test ajax edit
        data['description'] = 'edited description not bad'
        data['id'] = variable.id
        url = reverse('ajax_edit_indicator_variable')
        response = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(IndicatorVariable.objects.filter(description=data['description']).exists())

    def test_get_edit_indicator_variable(self):
        self._test_create_indicator_variable()
        variable = IndicatorVariable.objects.first()
        url = reverse('edit_indicator_variable', args=(variable.id, ))
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertIsInstance(response.context['variable_form'], IndicatorVariableForm)
        # now test ajax edit
        data = dict()
        data['id'] = variable.id
        url = reverse('ajax_edit_indicator_variable')
        response = self.client.get(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn(response.status_code, [200, 302])
        self.assertIsInstance(response.context['variable_form'], IndicatorVariableForm)

    def test_delete_indicator_variable(self):
        self._test_create_indicator_variable()
        variable = IndicatorVariable.objects.last()
        url = reverse('delete_indicator_variable', args=(variable.id,))
        data = self.variable_data.copy()
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(IndicatorVariable.objects.filter(id=variable.id).exists())
        # now test ajax edit
        variable = IndicatorVariable.objects.last()
        data['id'] = variable.id
        url = reverse('ajax_delete_indicator_variable')
        response = self.client.get(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(IndicatorVariable.objects.filter(id=data['id']).exists())

    def test_delete_indicator_variable_criteria(self):
        self._test_create_indicator_variable()
        criteria = IndicatorVariableCriteria.objects.last()
        url = reverse('delete_indicator_criteria', args=(criteria.id,))
        data = self.variable_data.copy()
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(IndicatorVariableCriteria.objects.filter(id=criteria.id).exists())

    def test_view_indicator_variables(self):
        indicator, data = self._test_create_indicator()
        url = reverse('view_indicator_variables', args=(indicator.id, ))
        response = self.client.get(url)
        self.assertIn(indicator.variables.first(), response.context['variables'])
        # test the json verson
        url = reverse('indicator_variables')
        response = self.client.get(url, data={'id': indicator.id})
        self.assertIn(indicator.variables.last().name, json.loads(response.content))

    def test_update_formulae_form(self):
        indicator, data = self._test_create_indicator()
        url = reverse('add_formula_page', args=(indicator.id, ))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.context['indicator_form'], IndicatorFormulaeForm)
        variables = list(IndicatorVariable.objects.filter(indicator=indicator).values_list('id', flat=True))
        data['formulae'] = '{{%s}}/{{%s}}*100' % tuple(list(IndicatorVariable.objects.values_list('name', flat=True)))
        response = self.client.post(url, data=data)
        self.assertTrue(Indicator.objects.filter(id=indicator.id, formulae=data['formulae']).exists())
        self.assertIn(response.status_code, [200, 302])

    def test_post_indicator_with_proper_params_creates(self):
        """post create variable then test create indicator"""
        self._test_create_indicator()

    def test_edit_indicator(self):
        indicator, data = self._test_create_indicator()
        url = reverse('edit_indicator_page', args=(indicator.id, ))
        data['name'] = 'edited_name_2_again'
        response = self.client.post(url, data=data)
        self.assertTrue(Indicator.objects.filter(name=data['name']).exists())
        self.assertTrue(response.status_code in [200, 302])

    def test_filter_indicators(self):
        # test filer list indicator page by quesionset
        # to do: something happening with test client here, would have to revisit this
        indicator, data = self._test_create_indicator()
        batch = Batch.objects.create(survey=self.survey, name='test batch', description='test desc')
        Indicator.objects.create(question_set=batch, survey=self.survey, name='indicator 2',
                                 description='description 2')
        url = reverse('list_indicator_page')
        response = self.client.get(url, {'survey': self.survey.id})
        self.assertIn('indicator/index.html', [t.name for t in response.templates])
        # indicators = Indicator.objects.filter(survey=self.survey)
        # # not the best way to test this but some issue with respons.context ... need to revisit this
        # for indicator in indicators:
        #     self.assertIn(indicator.name, response.content)
        # response = self.client.get(url, {'question_set': self.qset.id})
        # self.assertIn('indicator/index.html', [t.name for t in response.templates])
        # indicators = Indicator.objects.filter(survey=self.survey).exclude(question_set=batch)
        # for indicator in indicators:
        #     self.assertNotIn(indicator.name, response.content)

    def test_delete_indicators(self):
        indicator, data = self._test_create_indicator()
        url = reverse('delete_indicator_page', args=(indicator.id, ))
        response = self.client.get(url)
        self.assertFalse(Indicator.objects.filter(id=indicator.id).exists())
        self.assertTrue(response.status_code, [200, 302])

    def test_validate_indicator_formular(self):
        indicator, data = self._test_create_indicator()
        url = reverse('validate_formulae')
        response = self.client.post(url, data)
        self.assertJSONEqual(response.content, {'valid': True})

    def test_get_edit_indicator(self):
        indicator = Indicator.objects.create(
            name='ITN1', survey=self.survey, question_set=self.qset, description="bla")
        response = self.client.get(reverse('edit_indicator_page', kwargs={"indicator_id":indicator.id}))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('indicator/new.html', templates)
        self.assertIsNotNone(response.context['indicator_form'])
        self.assertIsInstance(response.context['indicator_form'], IndicatorForm)
        self.assertEqual(response.context['title'], "Edit Indicator")
        self.assertEqual(response.context['button_label'], "Save")

    def _bulk_answer_questions(self):
        answers = []
        n_quest = Question.objects.filter(answer_type=NumericalAnswer.choice_name()).first()
        t_quest = Question.objects.filter(answer_type=TextAnswer.choice_name()).first()
        m_quest = Question.objects.filter(answer_type=MultiChoiceAnswer.choice_name()).first()
        # first is numeric, then text, then multichioice
        answers = [{n_quest.id: 1, t_quest.id: 'Privet malishka, kach di la',  m_quest.id: 'Y'},
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
        self.assertEquals(TextAnswer.objects.first().to_text().lower(), 'Privet malishka, kach di la'.lower())
        m_answer = MultiChoiceAnswer.objects.first()
        self.assertEquals(m_answer.as_text.lower(), 'Y'.lower())
        self.assertEquals(m_answer.as_value,
                          str(QuestionOption.objects.get(text='Y', question__id=m_quest.id).order))

    def test_get_simple_indicator_chart_page(self):
        """Basic get simple indicator page. just empty graph mostly"""
        indicator, data = self._test_create_indicator()
        self.assertEquals(self.qset.id, indicator.question_set.id)
        self._bulk_answer_questions()
        url = reverse('simple_indicator_chart_page', args=(indicator.id, ))
        response = self.client.get(url)
        self.assertTrue(response.status_code, 200)
        self.assertIn('graph', response.context)
        self.assertIn('report', response.context)

    def test_get_download_analysis_page(self):
        indicator, data = self._test_create_indicator()
        self.assertEquals(self.qset.id, indicator.question_set.id)
        self._bulk_answer_questions()
        url = reverse('download_indicator_analysis', args=(indicator.id, ))
        response = self.client.get(url)
        self.assertTrue(response.status_code, 200)
        variables = IndicatorVariable.objects.all()
        response_text = response.content.lower()
        for variable in variables:
            self.assertIn(variable.name, response_text)
        for location in Location.objects.filter(type=LocationType.largest_unit()):
            self.assertIn(location.name.lower(), response_text)

    def test_permission_for_question_modules(self):
        self.assert_restricted_permission_for(reverse('list_indicator_page'))
        self.assert_restricted_permission_for(reverse('new_indicator_page'))

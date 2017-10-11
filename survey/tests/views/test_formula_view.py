from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from survey.forms.indicator import IndicatorFormulaeForm
from survey.models import (Survey, Batch, QuestionModule, Indicator, Question, QuestionOption,
                           QuestionSet, ResponseValidation, IndicatorVariable, IndicatorVariableCriteria)
from survey.views.indicators import INDICATOR_DOES_NOT_EXIST_MSG
from survey.tests.base_test import BaseTest


class IndicatorFormulaViewsTest(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        raj = self.assign_permission_to(raj, 'can_view_investigators')

        self.client.login(username='Rajni', password='I_Rock')
        self.survey = Survey.objects.create(name='survey name', description='survey descrpition',
                                            sample_size=10)
        self.qset = QuestionSet.objects.create(name="Females")
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest", constraint_message="message")
        self.batch = Batch.objects.create(
            order=1, name="Batch A", survey=self.survey)
        self.module = QuestionModule.objects.create(
            name='Education', description='Educational Module')
        self.indicator = Indicator.objects.create(name='Test Indicator', description="dummy",
                                                  display_on_dashboard=True, formulae="formulae",
                                                  question_set_id=self.qset.id, survey_id=self.survey.id)
        
        self.question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        self.question_1 = Question.objects.create(identifier='123.1', text="This is a question123.1",
                                                  answer_type='Numerical Answer',
                                                  qset_id=self.qset.id, response_validation_id=1)
        self.question_2 = Question.objects.create(identifier='123.2', text="This is a question123.2",
                                                  answer_type='Numerical Answer',
                                                  qset_id=self.qset.id, response_validation_id=1)
        self.question_3 = Question.objects.create(identifier='123.3', text="This is a question123.3",
                                                  answer_type='Numerical Answer',
                                                  qset_id=self.qset.id, response_validation_id=1)

    def test_indicator_variable(self):
        pass

    def test_get_new(self):
        response = self.client.get(reverse('add_formula_page', args=(self.indicator.id, )))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('indicator/formulae.html', templates)
        self.assertEquals(reverse('list_indicator_page'), response.context['cancel_url'])
        self.assertEquals(self.indicator, response.context['indicator'])
        self.assertEquals('Save', response.context['button_label'])
        self.assertIsInstance(response.context['indicator_form'], IndicatorFormulaeForm)

    def test_create_indicator_formular(self):
        formular_url = reverse('add_formula_page', args=(self.indicator.id, ))
        response = self.client.get(formular_url)
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('indicator/formulae.html', templates)
        response = self.client.post(formular_url, data={})

    def test_get_knows_to_throw_error_message_if_indicator_does_not_exist(self):
        response = self.client.get(reverse('add_formula_page', args=(self.indicator.id,)))
        self.assertEqual(200, response.status_code)
        message = INDICATOR_DOES_NOT_EXIST_MSG
        self.failUnlessEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('list_indicator_page'), 302, 200)

    def test_get_knows_to_throw_error_message_if_indicator_does_not_exist(self):
        # response = self.client.get('/indicators/%s/formula/new/' % 200)
        indicator_obj = Indicator.objects.create(name='Test Indicator6', description="dummy6",display_on_dashboard=True,formulae="formulae2",
                                                  question_set_id=self.qset.id, survey_id=self.survey.id)
        response = self.client.get(reverse('add_formula_page',kwargs={"indicator_id" : indicator_obj.id}))
        self.assertEqual(200, response.status_code)

        message = "The indicator requested does not exist."

        self.failUnlessEqual(response.status_code, 200)
        self.assertRedirects(response, '/indicators/', 302)

    def test_post_new_for_percentage_indicator_with_multichoice_numerator_and_denominator_question(self):
        multichoice_question = Question.objects.create(identifier='aman', text="This is a question123.4",
                                                       answer_type='Numerical Answer', qset_id=self.qset.id,
                                                       response_validation_id=1)

        option_1 = QuestionOption.objects.create(
            question=multichoice_question, text='Yes', order=1)
        option_2 = QuestionOption.objects.create(
            question=multichoice_question, text='No', order=2)
        option_3 = QuestionOption.objects.create(
            question=multichoice_question, text='Maybe', order=3)
        option_4 = QuestionOption.objects.create(
            question=multichoice_question, text='Not Known', order=4)

        data = {'numerator': multichoice_question.id,
                'denominator': multichoice_question.id,
                'numerator_options': [option_1.id, option_2.id],
                'denominator_options': [option_1.id, option_2.id, option_3.id, option_4.id],
                'denominator_type': 'QUESTION'}

        all_numerator_formula_options = [option_1, option_2]
        excluded_numerator_formula_options = [option_3, option_4]
        all_denominator_formula_options = [
            option_1, option_2, option_3, option_4]
        indicator = Indicator.objects.create(name='Test Indicator', description="dummy",display_on_dashboard=True,formulae="formulae",
                                                  question_set_id=self.qset.id, survey_id=self.survey.id)
        # BatchQuestionOrder.objects.create(batch=self.batch, question=multichoice_question, order=4)
        new_formula_url = reverse('add_formula_page', args=(indicator.id,))
        # new_formula_url = '/indicators/%s/formula/new/' % self.indicator.id
        response = self.client.get(reverse('add_formula_page',kwargs={"indicator_id" : indicator.id}))
        self.assertEqual(200, response.status_code)

        response = self.client.post(new_formula_url, data=data)
        message = "Formula successfully added to indicator %s." % self.indicator.name

        # self.assertIn(message, response.content)

        # self.assertIn(message, response.cookies['messages'].value)
        # saved_formula = Formula.objects.filter(numerator=multichoice_question, denominator=multichoice_question,
        #                                        indicator=self.indicator)

        # saved_numerator_question_options = saved_formula[
        #     0].numerator_options.all()
        # saved_denominator_question_options = saved_formula[
        #     0].denominator_options.all()

        # self.failUnless(saved_formula)
        # [self.assertIn(option, saved_numerator_question_options)
        #  for option in all_numerator_formula_options]
        # [self.assertNotIn(option, saved_numerator_question_options)
        #  for option in excluded_numerator_formula_options]
        # [self.assertIn(option, saved_denominator_question_options)
        #  for option in all_denominator_formula_options]

    def test_post_new_for_count_indicator_with_multichoice_count_question(self):

        # multichoice_question = Question.objects.create(identifier='123.4', text="This is a question123.4", answer_type='Numerical Answer',
        #                                                group=self.group, batch=self.batch, module=self.question_mod)
        multichoice_question = Question.objects.create(identifier='123.4', text="This is a question123.4", answer_type='Numerical Answer',
                                                  qset_id=self.qset.id, response_validation_id=1)
        option_1 = QuestionOption.objects.create(
            question=multichoice_question, text="OPTION 1", order=1)
        option_2 = QuestionOption.objects.create(
            question=multichoice_question, text="OPTION 2", order=2)
        option_3 = QuestionOption.objects.create(
            question=multichoice_question, text="Others", order=3)

        count_indicator = Indicator.objects.create(name='Test Indicator', description="dummy",display_on_dashboard=True,formulae="formulae",
                                                  question_set_id=self.qset.id, survey_id=self.survey.id)

        data = {'numerator': multichoice_question.id,
                'denominator': multichoice_question.id,
                'denominator_options': [option_1.id, option_2.id, option_3.id],
                'denominator_type': 'QUESTION'}

        all_formula_options = [option_1, option_2, option_3]

        # new_formula_url = '/indicators/%s/formula/new/' % count_indicator.id
        new_formula_url = reverse('add_formula_page', args=(count_indicator.id,))
        response = self.client.post(new_formula_url, data=data)
        message = "Formula successfully added to indicator %s." % self.indicator.name

        # self.assertIn(message, response.cookies['messages'].value)
        # # saved_formula = Formula.objects.filter(
        # #     count=multichoice_question, indicator=count_indicator)
        # saved_formula = Formula.objects.filter(numerator=multichoice_question, denominator=multichoice_question,
        #                                        indicator=self.indicator)



        # self.failUnless(saved_formula)
        # saved_formula_question_options = saved_formula[
        #     0].denominator_options.all()

        # [self.assertIn(option, saved_formula_question_options)
        #  for option in all_formula_options]

    # def test_delete_removes_formula_and_redirects_to_new_formula_page_with_success_message(self):
    #     delete_url = '/indicators/%s/formula/%s/delete/' % (
    #         self.indicator.id, self.existing_formula.id)
    #     response = self.client.get(delete_url)

    #     redirect_url = '/indicators/%s/formula/new/' % self.indicator.id

    #     self.failIf(Formula.objects.filter(numerator=self.question_1, denominator=self.question_2,
    #                                        indicator=self.indicator))
    #     self.assertIn("Formula successfully deleted.",
    #                   response.cookies['messages'].value)
    #     self.assertRedirects(response, redirect_url, 302, 200)

    # def test_delete_removes_formula_and_redirects_to_new_formula_page_with_error_message_if_non_existent_formula(self):
    #     non_existent_formula = '200'
    #     delete_url = '/indicators/%s/formula/%s/delete/' % (
    #         self.indicator.id, non_existent_formula)
    #     response = self.client.get(delete_url)

    #     redirect_url = '/indicators/%s/formula/new/' % self.indicator.id
    #     self.assertIn("Formula for indicator does not exist.",
    #                   response.cookies['messages'].value)
    #     self.assertRedirects(response, redirect_url, 302, 200)

    # def test_permissions_required(self):
    #     delete_url = '/indicators/%s/formula/%s/delete/' % (
    #         self.indicator.id, self.existing_formula.id)
    #     self.assert_restricted_permission_for(delete_url)

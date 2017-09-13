from django.contrib.auth.models import User
from django.test import Client
from survey.forms.indicator import IndicatorForm
from survey.forms.filters import IndicatorFilterForm
from survey.models import QuestionModule, Batch, Indicator, Survey, Question, QuestionSet
from survey.tests.base_test import BaseTest
from django.core.urlresolvers import reverse


class IndicatorViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        # self.module = QuestionModule.objects.create(name="Health")
        self.survey = Survey.objects.create(name="Health survey")
        # self.batch = Batch.objects.create(name="Health", survey=self.survey)
        self.qset = QuestionSet.objects.create(name="qset",description="blahblah")
        # question_mod = QuestionModule.objects.create(
        #     name="Test question name", description="test desc")
        # batch = Batch.objects.create(order=1)
        
        self.form_data = {
                          'name': 'Health',
                          'description': 'some description',
                          'question_set' : self.qset,                          
                          'survey': self.survey.id}

        User.objects.create_user(
            username='useless', email='demo4@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('demo4', 'demo4@kant.com', 'demo4'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')
        self.client.login(username='demo4', password='demo4')

    def test_get_new_indicator(self):
        response = self.client.get(reverse('new_indicator_page'))
        # self.failUnlessEqual(response.status_code, 200)
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('indicator/new.html', templates)
        self.assertIsNotNone(response.context['indicator_form'])
        self.assertIsInstance(
            response.context['indicator_form'], IndicatorForm)
        self.assertIn(response.context['title'], "Add Indicator")
        self.assertIn(response.context['button_label'], "Create")
        self.assertIn(response.context['action'], reverse('new_indicator_page'))    

    def test_post_indicator_creates_an_indicator_and_returns_success(self):
        data = self.form_data.copy()
        del data['survey']
        self.failIf(Indicator.objects.filter(**data))

        another_survey = Survey.objects.create(name="Education survey")
        data['survey'] = another_survey.id
        response = self.client.post(reverse('new_indicator_page'), data=data)

        error_message = "Indicator was not created."
        self.assertIn(error_message, response.content)

    def test_get_edit_indicator(self):
        indicator = Indicator.objects.create(
            name='ITN1', survey=self.survey, question_set=self.qset, description="bla")
        response = self.client.get(reverse('edit_indicator_page',kwargs={"indicator_id":indicator.id}))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('indicator/new.html', templates)
        self.assertIsNotNone(response.context['indicator_form'])
        self.assertIsInstance(
            response.context['indicator_form'], IndicatorForm)
        self.assertEqual(response.context['title'], "Edit Indicator")
        self.assertEqual(response.context['button_label'], "Save")

    def test_post_edit_indicator_updates_and_returns_success(self):
        survey = Survey.objects.create(name='survey')
        indicator = Indicator.objects.create(
            name='ITN1', survey=self.survey, question_set=self.qset, description="bla")        
        #survey = Survey.objects.create(name='Survey A')        
        # self.batch = Batch.objects.create(name='Batch A', survey=survey)
        self.qset = QuestionSet.objects.create(name="qset",description="blahblah")
        # self.module = QuestionModule.objects.create(name="Health")
        self.form_data = {
                          'name': 'Health',
                          'description': 'some description',
                          'question_set' : self.qset,                          
                          # 'batch': self.batch.id,
                          'survey': self.survey.id}

        data = self.form_data.copy()
        del data['survey']
        self.failIf(Indicator.objects.filter(**data))
        response = self.client.post(reverse('edit_indicator_page',kwargs={"indicator_id":indicator.id}), data=self.form_data)

        self.failUnless(Indicator.objects.filter(
            name=self.form_data['name'], description=self.form_data['description']))
        self.assertRedirects(response, expected_url=reverse('list_indicator_page'))
        success_message = "Indicator successfully edited."
        self.assertIn(success_message, response.cookies['messages'].value)

    def test_post_edit_indicator_updates_and_returns_error(self):
        survey = Survey.objects.create(name='survey')
        self.qset = QuestionSet.objects.create(name="qset",description="blahblah")
        # self.module = QuestionModule.objects.create(name="Health")
        # self.batch = Batch.objects.create(name='Batch A', survey=self.survey)
        indicator = Indicator.objects.create(
            name='ITN1', survey=self.survey, question_set=self.qset, description="bla")        
        self.form_data = {
                          'name': 'Health',
                          'description': 'some description',
                          'question_set' : self.qset,                          
                          # 'batch': self.batch.id,
                          'survey': self.survey.id}

        data = self.form_data.copy()
        del data['survey']
        self.failIf(Indicator.objects.filter(**data))
        response = self.client.post(reverse('edit_indicator_page',kwargs={"indicator_id":indicator.id}), data=self.form_data)

        self.failIf(Indicator.objects.filter(name=self.form_data[
                    'name'], description=self.form_data['description']))
        self.failUnlessEqual(response.status_code, 200)
        error_message = "Indicator was not successfully edited."
        self.assertIn(error_message, response.content)

    def test_post_indicator_fails_and_returns_error_message(self):
        data = self.form_data.copy()
        del data['survey']
        self.failIf(Indicator.objects.filter(**data))
        response = self.client.post(reverse('new_indicator_page'), data=self.form_data)
        # self.failUnless(Indicator.objects.filter(**data))
        self.failUnless(Indicator.objects.filter(
            name=self.form_data['name'], description=self.form_data['description']))
        self.assertRedirects(response, reverse('list_indicator_page'), 302, 200)
        success_message = "Indicator successfully created."
        self.assertIn(success_message, response.cookies['messages'].value)

    def test_permission_for_question_modules(self):
        self.assert_restricted_permission_for(reverse('list_indicator_page'))
        self.assert_restricted_permission_for(reverse('new_indicator_page'))

    def test_get_indicator_index(self):
        another_form_data = self.form_data.copy()
        another_form_data['name'] = 'Education'
        another_form_data['description'] = 'bla'
        another_form_data['question_set'] = self.qset
        # another_form_data['module'] = self.module
        # another_form_data['batch'] = self.batch
        del another_form_data['survey']

        education_indicator = Indicator.objects.create(**another_form_data)
        response = self.client.get(reverse('list_indicator_page'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('indicator/index.html', templates)
        self.assertIsInstance(
            response.context['indicator_filter_form'], IndicatorFilterForm)
        self.assertIn(education_indicator, response.context['indicators'])

    def test_post_filter_indicators_by_survey(self):
        survey = Survey.objects.create(name='survey')
        qset = QuestionSet.objects.create(name='qset',description="bla")
        # batch_s = Batch.objects.create(name='batch survey', survey=survey)
        # batch = Batch.objects.create(name='batch s')
        # module = QuestionModule.objects.create(name="module")
        indicator_s = Indicator.objects.create(
            name='ITN', survey=self.survey, question_set=self.qset, description="bla")
        indicator = Indicator.objects.create(
            name='ITN1', survey=self.survey, question_set=self.qset, description="bla")

        response = self.client.get(
            reverse('list_indicator_page'), data={'survey': survey.id, 'question_set': qset.id})
        self.failUnlessEqual(response.status_code, 200)
        self.assertIsInstance(
            response.context['indicator_filter_form'], IndicatorFilterForm)
        self.assertEqual(2, len(response.context['indicators']))
        self.assertIn(indicator_s, response.context['indicators'])
        self.assertIn(indicator, response.context['indicators'])

    def test_post_filter_indicators_by_batch(self):
        survey = Survey.objects.create(name='survey')
        qset = QuestionSet.objects.create(name='qset',description="bla")
        batch_s = Batch.objects.create(name='batch survey', survey=survey)
        batch_s2 = Batch.objects.create(name='batch survey 2', survey=survey)
        batch = Batch.objects.create(name='batch s')
        # module = QuestionModule.objects.create(name="module")
        indicator_s = Indicator.objects.create(
            name='ITN', survey=self.survey, question_set=self.qset, description="bla")
        indicator_s2 = Indicator.objects.create(
            name='ITN2', survey=self.survey, question_set=self.qset, description="bla")
        indicator = Indicator.objects.create(
            name='ITN3', survey=self.survey, question_set=self.qset, description="bla")

        response = self.client.get(
            reverse('list_indicator_page'), data={'survey': 'All', 'question_set': qset.id})
        self.failUnlessEqual(response.status_code, 200)
        self.assertIsInstance(
            response.context['indicator_filter_form'], IndicatorFilterForm)
        self.assertIn(indicator_s, response.context['indicators'])
        self.assertEqual(3, len(response.context['indicators']))
        self.assertIn(indicator_s2, response.context['indicators'])
        self.assertIn(indicator, response.context['indicators'])

    def test_should_get_all_indicators_in_a_given_module_when_module_is_given(self):
        survey = Survey.objects.create(name='survey')
        qset = QuestionSet.objects.create(name='qset',description='bla')
        # batch_s = Batch.objects.create(name='batch survey', survey=survey)
        module = QuestionModule.objects.create(name="module")
        # module_1 = QuestionModule.objects.create(name="module")
        self.qset = QuestionSet.objects.create(name="qset",description="blahblah")

        indicator_1 = Indicator.objects.create(name="indicator name 1", description="demo4 indicator 1",
                                               question_set=self.qset, survey=survey)
        indicator_2 = Indicator.objects.create(name="indicator name 1", description="demo4 indicator 1",                                               
                                               question_set=self.qset, survey=survey)

        response = self.client.get(
            reverse('list_indicator_page'), data={'survey': 'All', 'qustion_set': 'All', 'module': module.id})
        self.failUnlessEqual(response.status_code, 200)
        self.assertEqual(2, len(response.context['indicators']))
        self.assertIn(indicator_1, response.context['indicators'])
        self.assertIn(indicator_2, response.context['indicators'])

    def test_should_get_all_indicators_in_a_given_module_when_module_and_batch_is_given(self):
        survey = Survey.objects.create(name='survey')
        qset = QuestionSet.objects.create(name='qset',description="bla")
        # batch_s = Batch.objects.create(name='batch survey', survey=survey)
        # module = QuestionModule.objects.create(name="module")
        # module_1 = QuestionModule.objects.create(name="module")
        self.qset = QuestionSet.objects.create(name="qset",description="blahblah")

        indicator_1 = Indicator.objects.create(name="indicator name 1", description="demo4 indicator 1",question_set=self.qset,
                                               survey=survey)
        indicator_2 = Indicator.objects.create(name="indicator name 1", description="demo4 indicator 1",
                                               question_set=self.qset,
                                                survey=survey)

        response = self.client.get(
            reverse('list_indicator_page'), data={'survey': 'All', 'question_set': qset.id})
        self.failUnlessEqual(response.status_code, 200)
        self.assertEqual(2, len(response.context['indicators']))
        self.assertIn(indicator_1, response.context['indicators'])
        self.assertIn(indicator_2, response.context['indicators'])

    def test_should_get_all_indicators_in_a_given_module_when_all_are_given(self):
        survey = Survey.objects.create(name='survey')
        qset = QuestionSet.objects.create(name='qset', description='bla')
        # batch_s = Batch.objects.create(name='batch survey', survey=survey)
        # module = QuestionModule.objects.create(name="module")
        # module_1 = QuestionModule.objects.create(name="module")
        self.qset = QuestionSet.objects.create(name="qset",description="blahblah")

        indicator_1 = Indicator.objects.create(name="indicator name 1", description="demo4 indicator 1",
                                               question_set=self.qset,
                                                survey=survey)
        indicator_2 = Indicator.objects.create(name="indicator name 1", description="demo4 indicator 1",
                                               question_set=qset,
                                                survey=survey)

        response = self.client.get(reverse('list_indicator_page'),
                                   data={'survey': survey.id, 'question_set': qset.id})
        self.failUnlessEqual(response.status_code, 200)
        self.assertEqual(2, len(response.context['indicators']))
        self.assertIn(indicator_1, response.context['indicators'])
        self.assertIn(indicator_2, response.context['indicators'])
    def test_delete_indicator(self):
        survey = Survey.objects.create(name='survey')
        # batch_s = Batch.objects.create(name='batch survey', survey=survey)
        # module = QuestionModule.objects.create(name="module")
        # module_1 = QuestionModule.objects.create(name="module")
        qset = QuestionSet.objects.create(name='qset', description='bla')
        self.qset = QuestionSet.objects.create(name="qset",description="blahblah")

        indicator_1 = Indicator.objects.create(name="indicator name 1", description="demo4 indicator 1",
                                               question_set=self.qset,
                                                survey=survey)
        indicator_2 = Indicator.objects.create(name="indicator name 1", description="demo4 indicator 1",
                                               question_set=self.qset,
                                               survey=survey)

        response = self.client.get(reverse('delete_indicator_page',kwargs={"indicator_id":indicator_1.id}))
        recovered_indicator = Indicator.objects.filter(id=indicator_1.id)
        self.assertRedirects(response, expected_url=reverse('list_indicator_page'), status_code=302,
                             target_status_code=200, msg_prefix='')
        self.assertIn('Indicator successfully deleted.',
                      response.cookies['messages'].value)
        self.failIf(recovered_indicator)
        self.failUnless(Indicator.objects.get(id=indicator_2.id))

    def test_should_not_delete_indicator_with_a_formula(self):
        survey = Survey.objects.create(name='survey')
        # batch_s = Batch.objects.create(name='batch survey', survey=survey)
        # module = QuestionModule.objects.create(name="module")
        # qset = QuestionSet.objects.create(name="qset")
        qset = QuestionSet.objects.create(name='qset', description='bla')
        indicator_1 = Indicator.objects.create(name="indicator name 1", description="demo4 indicator 1",
                                               survey=survey,question_set=qset
                                               )

        response = self.client.get(reverse('delete_indicator_page',kwargs={"indicator_id":indicator_1.id}))
        self.failIf(Indicator.objects.filter(id=indicator_1.id))
        
        self.assertIn('Indicator successfully deleted.',
                      response.cookies['messages'].value)

    def test_restricted_perms_to_delete_indicator(self):
        self.assert_restricted_permission_for(reverse('delete_indicator_page',kwargs={"indicator_id":999999}))

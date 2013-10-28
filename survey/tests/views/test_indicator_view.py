from django.contrib.auth.models import User
from django.test import Client
from survey.forms.indicator import IndicatorForm
from survey.models import QuestionModule, Batch, Indicator
from survey.tests.base_test import BaseTest


class IndicatorViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        module = QuestionModule.objects.create(name="Health")
        batch = Batch.objects.create(name="Health")

        self.form_data = {'module': module.id,
                          'name': 'Health',
                          'description': 'some description',
                          'measure': '%',
                          'batch': batch.id}

        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')
        self.client.login(username='Rajni', password='I_Rock')

    def test_get_new_indicator(self):
        response = self.client.get('/indicators/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('indicator/new.html', templates)
        self.assertIsNotNone(response.context['indicator_form'])
        self.assertIsInstance(response.context['indicator_form'], IndicatorForm)
        self.assertEqual(response.context['title'], "Add Indicator")
        self.assertEqual(response.context['button_label'], "Save")
        self.assertEqual(response.context['action'], "/indicators/new/")

    def test_post_indicator_ceates_an_indicator_and_returns_success(self):
        self.failIf(Indicator.objects.filter(**self.form_data))
        response = self.client.post('/indicators/new/', data=self.form_data)
        self.failUnless(Indicator.objects.filter(**self.form_data))
        self.assertRedirects(response, "/indicators/", 302, 200)
        success_message = "Indicator successfully created."
        self.assertIn(success_message, response.cookies['messages'].value)

    def test_permission_for_question_modules(self):
        self.assert_restricted_permission_for('/indicators/')
        self.assert_restricted_permission_for('/indicators/new/')
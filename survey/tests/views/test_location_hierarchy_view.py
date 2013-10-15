from django.contrib.auth.models import User
from django.test import Client
from survey.forms.location_hierarchy import LocationHierarchyForm
from survey.tests.base_test import BaseTest


class LocationHierarchyTest(BaseTest):

    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')
        self.client.login(username='Rajni', password='I_Rock')

    def test_should_render_success_code(self):
        response = self.client.get('/add_location_hierarchy/')
        self.assertEqual(200,response.status_code)

    def test_should_render_template(self):
        response = self.client.get('/add_location_hierarchy/')
        self.assertEqual(200,response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('location_hierarchy/new.html', templates)

    def test_should_render_form_instance(self):
        response = self.client.get('/add_location_hierarchy/')
        self.assertEqual(200,response.status_code)
        self.assertIsInstance(response.context['hierarchy_form'],LocationHierarchyForm)

    def test_should_render_context_data(self):
        response = self.client.get('/add_location_hierarchy/')
        self.assertEqual(200,response.status_code)
        self.assertEqual(response.context['button_label'],"Create Hierarchy")
        self.assertEqual(response.context['id'],"hierarchy-form")
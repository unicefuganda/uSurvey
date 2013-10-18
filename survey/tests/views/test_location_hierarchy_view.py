from django.contrib.auth.models import User
from django.forms.formsets import formset_factory
from django.test import Client
from rapidsms.contrib.locations.models import LocationType, Location
from survey.forms.location_details import LocationDetailsForm
from survey.forms.location_hierarchy import LocationHierarchyForm, BaseArticleFormSet
from survey.models import LocationTypeDetails
from survey.tests.base_test import BaseTest


class LocationHierarchyTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')
        self.client.login(username='Rajni', password='I_Rock')
        country = LocationType.objects.create(name='Country', slug='country')
        self.uganda = Location.objects.create(name='Uganda', type=country)
        self.DetailsFormSet = formset_factory(LocationDetailsForm, formset=BaseArticleFormSet)

    def test_should_render_success_code(self):
        response = self.client.get('/add_location_hierarchy/')
        self.assertEqual(200, response.status_code)

    def test_should_render_template(self):
        response = self.client.get('/add_location_hierarchy/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('location_hierarchy/new.html', templates)

    def test_should_render_form_instance(self):
        response = self.client.get('/add_location_hierarchy/')
        self.assertEqual(200, response.status_code)
        self.assertIsInstance(response.context['hierarchy_form'], LocationHierarchyForm)

    def test_should_render_context_data(self):
        response = self.client.get('/add_location_hierarchy/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.context['button_label'], "Create Hierarchy")
        self.assertEqual(response.context['id'], "hierarchy-form")
        #self.assertIsInstance(response.context['details_formset'],self.DetailsFormSet)

    def test_should_redirect_to_home_page_after_post(self):
        levels_data = {'country': self.uganda.id, 'form-0-levels': 'Region', 'form-TOTAL_FORMS': 1,
                       'form-INITIAL_FORMS': 0}
        response = self.client.post('/add_location_hierarchy/', data=levels_data)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='')

    def test_should_save_location_type_after_post(self):
        levels_data = {'country': self.uganda.id, 'form-0-levels': 'Region', 'form-TOTAL_FORMS': 1,
                       'form-INITIAL_FORMS': 0}
        response = self.client.post('/add_location_hierarchy/', data=levels_data)
        location_types = LocationType.objects.all()
        self.assertEqual(2, location_types.count())
        location_type_created = LocationType.objects.get(name='Region')
        self.failUnless(location_type_created)

    def test_should_save_location_types_if_multiple_levels_after_post(self):
        levels_data = {'country': self.uganda.id,
                       'form-0-levels': 'Region',
                       'form-1-levels': 'District',
                       'form-TOTAL_FORMS': 2,
                       'form-INITIAL_FORMS': 0,
        }

        response = self.client.post('/add_location_hierarchy/', data=levels_data)
        location_types = LocationType.objects.all()
        self.assertEqual(3, location_types.count())
        location_type_created = LocationType.objects.get(name='Region')
        self.failUnless(location_type_created)
        location_type_created = LocationType.objects.get(name='District')
        self.failUnless(location_type_created)

    def test_should_save_any_location_types_if_multiple_levels_after_post_and_error_in_one(self):
        levels_data = {'country': self.uganda.id,
                       'form-0-levels': 'Region',
                       'form-0-required': 'on',
                       'form-1-levels': 'District',
                       'form-1-has_code': 'on',
                       'form-TOTAL_FORMS': 2,
                       'form-INITIAL_FORMS': 0,
        }

        response = self.client.post('/add_location_hierarchy/', data=levels_data)
        location_types = LocationType.objects.all()
        self.assertEqual(1, location_types.count())

    def test_should_save_country_on_location_type_details_after_post(self):
        levels_data = {'country': self.uganda.id, 'form-0-levels': 'Region', 'form-TOTAL_FORMS': 1,
                       'form-INITIAL_FORMS': 0}
        response = self.client.post('/add_location_hierarchy/', data=levels_data)
        location_types = LocationType.objects.all()
        self.assertEqual(2, location_types.count())
        location_type_details = LocationTypeDetails.objects.all()
        self.assertEqual(1, location_type_details.count())
        location_type_details = location_type_details[0]
        self.failUnless(location_type_details)
        self.assertEqual(location_type_details.country,self.uganda)

    def test_should_be_invalid_if_country_is_blank_after_post(self):
        levels_data = {'form-0-levels': 'Region', 'form-TOTAL_FORMS': 1,
                       'form-INITIAL_FORMS': 0}
        response = self.client.post('/add_location_hierarchy/', data=levels_data)
        location_types = LocationType.objects.all()
        self.assertEqual(1, location_types.count())

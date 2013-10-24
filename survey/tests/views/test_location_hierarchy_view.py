from django.contrib.auth.models import User
from django.forms.formsets import formset_factory
from django.template.defaultfilters import slugify
from django.test import Client
from mock import patch
from rapidsms.contrib.locations.models import LocationType, Location
from survey.forms.location_details import LocationDetailsForm
from survey.forms.location_hierarchy import LocationHierarchyForm, BaseArticleFormSet
from survey.forms.upload_locations import UploadLocationForm
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
        self.assertIn("Location Hierarchy successfully created.", response.cookies['messages'].value)

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


    def test_saving_already_existing_location_hierarchy_type(self):
        levels_data = {'country': self.uganda.id, 'form-0-levels': 'Region', 'form-TOTAL_FORMS': 1,
                       'form-INITIAL_FORMS': 0}
        region = LocationType.objects.create(name=levels_data['form-0-levels'], slug =slugify(levels_data['form-0-levels']))
        response = self.client.post('/add_location_hierarchy/', data=levels_data)
        location_types = LocationType.objects.all()
        self.assertEqual(2, location_types.count())
        self.assertIn(region, location_types)
        self.assertIn(self.uganda.type, location_types)

    def test_saving_multiple_location_hierarchy_types(self):
        levels_data = {'country': self.uganda.id, 'form-0-levels': 'Region',
                       'form-1-levels': 'Hill', 'form-1-required':'on',
                       'form-1-has_code':'on', 'form-1-code':'0001',
                       'form-TOTAL_FORMS': 2,
                       'form-INITIAL_FORMS': 0}
        response = self.client.post('/add_location_hierarchy/', data=levels_data)
        location_types = LocationType.objects.all()
        self.assertEqual(3, location_types.count())
        region = LocationType.objects.get(name=levels_data['form-0-levels'])
        self.failUnless(region)
        hill = LocationType.objects.get(name=levels_data['form-1-levels'])
        self.failUnless(hill)
        hill_details = LocationTypeDetails.objects.get(location_type=hill)
        self.assertEqual(True, hill_details.required)
        self.assertEqual(True, hill_details.has_code)
        self.assertEqual(levels_data['form-1-code'], hill_details.code)
        self.assertEqual(self.uganda, hill_details.country)

    def test_permission_access(self):
        self.assert_restricted_permission_for('/add_location_hierarchy/')


class UploadLocationsTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')
        self.client.login(username='Rajni', password='I_Rock')
        country = LocationType.objects.create(name='Country', slug='country')
        self.uganda = Location.objects.create(name='Uganda', type=country)
        self.some_other_country = Location.objects.create(name='SomeOtherCountry', type=country)
        self.location_type1 = LocationType.objects.create(name = 'Region',slug='region')
        self.location_type_details1 = LocationTypeDetails.objects.create(required=False,has_code=False,code='',location_type=self.location_type1,country=self.uganda)

        self.location_type2 = LocationType.objects.create(name = 'District',slug='district')
        self.location_type_details2 = LocationTypeDetails.objects.create(required=False,has_code=False,code='',location_type=self.location_type2,country=self.uganda)

        self.location_type3 = LocationType.objects.create(name = 'County',slug='county')
        self.location_type_details3 = LocationTypeDetails.objects.create(required=False,has_code=False,code='',location_type=self.location_type3,country=self.uganda)

        self.filename = 'uganda.csv'
        self.filedata = [["Region", "District", "County"], ["0","1","2"], ["3","4","5"], ["6","7","8"]]
        self.write_to_csv('wb', self.filedata, self.filename)
        self.file = open(self.filename, 'rb')


    def test_should_render_success_code(self):
        response = self.client.get('/locations/upload/')
        self.assertEqual(200, response.status_code)

    def test_should_render_template(self):
        response = self.client.get('/locations/upload/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('location_hierarchy/upload.html', templates)

    def test_should_render_context_data(self):
        response = self.client.get('/locations/upload/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.context['button_label'], "Save")
        self.assertEqual(response.context['id'], "upload-locations-form")
        self.assertEqual(response.context['country_name'], self.uganda.name)
        self.assertIsInstance(response.context['upload_form'],UploadLocationForm)

    def test_should_not_render_country_type_in_location_types_in_context_data(self):
        response = self.client.get('/locations/upload/')
        self.assertEqual(200, response.status_code)
        [self.assertIn(location_type , response.context['location_types']) for location_type in LocationType.objects.exclude(name__iexact='country')]
        [self.assertNotIn(location_type , response.context['location_types']) for location_type in LocationType.objects.filter(name__iexact='country')]


    def test_should_render_error_message_if_no_type_and_details_yet(self):
        LocationType.objects.all().delete()
        LocationTypeDetails.objects.all().delete()
        response = self.client.get('/locations/upload/')
        self.assertEqual(302, response.status_code)
        self.assertIn('No location hierarchy added yet.', response.cookies['messages'].value)

    def test_should_redirect_after_post(self):
         data={u'save_button': [u''], u'csrfmiddlewaretoken': [u'db932acf6e42fabb23ad545c71751b0a'],'file': self.file}
         response = self.client.post('/locations/upload/', data=data)
         self.assertRedirects(response, '/locations/upload/', status_code=302, target_status_code=200, msg_prefix='')

    @patch('survey.views.location_upload_view_helper.UploadLocation.upload')
    def test_should_give_success_message_if_csv_uploaded(self, mock_upload):
         mock_upload.return_value = (True, 'Successfully uploaded')
         data = {u'save_button': [u''], u'csrfmiddlewaretoken': [u'db932acf6e42fabb23ad545c71751b0a'], 'file': self.file }
         response = self.client.post('/locations/upload/', data=data)
         assert mock_upload.called
         self.assertIn('Successfully uploaded', response.cookies['messages'].value)

    def test_should_upload_csv_sucess(self):
         data = {u'save_button': [u''], u'csrfmiddlewaretoken': [u'db932acf6e42fabb23ad545c71751b0a'], 'file': self.file }
         response = self.client.post('/locations/upload/', data=data)
         types = self.filedata[0]
         for locations in self.filedata[1:]:
             [self.failUnless(Location.objects.filter(name=location_name, type__name__iexact=types[index].lower())) for index, location_name in enumerate(locations)]
         self.assertIn('Successfully uploaded', response.cookies['messages'].value)

    def test_permission_access(self):
        self.assert_restricted_permission_for('/locations/upload/')

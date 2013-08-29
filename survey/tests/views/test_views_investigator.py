import json

from django.test import TestCase
from django.test.client import Client
from mock import *
from django.template.defaultfilters import slugify

from rapidsms.contrib.locations.models import Location, LocationType
from survey.forms.investigator import InvestigatorForm
from survey.models_file import *
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

class InvestigatorTest(TestCase):
    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_investigators', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)

        self.client.login(username='Rajni', password='I_Rock')

    def assert_restricted_permission_for(self, url):
        self.client.logout()

        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)

        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%url, status_code=302, target_status_code=200, msg_prefix='')


class InvestigatorsViewTest(InvestigatorTest):
    def test_new(self):
        country = LocationType.objects.create(name = 'Country', slug = 'country')
        city = LocationType.objects.create(name = 'City', slug = 'city')

        uganda = Location.objects.create(name='Uganda', type = country)
        abim = Location.objects.create(name='Abim', tree_parent = uganda, type = city)
        kampala = Location.objects.create(name='Kampala', tree_parent = uganda, type = city)
        kampala_city = Location.objects.create(name='Kampala City', tree_parent = kampala, type = city)

        response = self.client.get('/investigators/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/investigator_form.html', templates)
        self.assertEquals(response.context['action'], '/investigators/new/')
        self.assertEquals(response.context['country_phone_code'], COUNTRY_PHONE_CODE)
        self.assertEquals(response.context['title'], 'New Investigator')
        self.assertEquals(response.context['id'], 'create-investigator-form')
        self.assertEquals(response.context['button_label'], 'Create Investigator')
        self.assertEquals(response.context['loading_text'], 'Creating...')

        locations = response.context['locations'].get_widget_data()
        self.assertEquals(len(locations.keys()), 2)
        self.assertEquals(locations.keys()[0], 'country')
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

        self.assertEquals(len(locations['city']), 0)

    def test_get_district_location_returns_all_locations_if_parent_not_specified(self):
        uganda = Location.objects.create(name="Uganda")
        uganda_duplicate = Location.objects.create(name="Uganda something else")
        response = self.client.get('/investigators/locations')
        self.failUnlessEqual(response.status_code, 200)
        locations = json.loads(response.content)
        self.failUnlessEqual(locations, {
            'Uganda': uganda.id,
            'Uganda something else': uganda_duplicate.id,
        })

    def test_get_district_location_returns_all_locations_if_parent_empty(self):
        uganda = Location.objects.create(name="Uganda")
        uganda_duplicate = Location.objects.create(name="Uganda something else")
        response = self.client.get('/investigators/locations?parent=')
        self.failUnlessEqual(response.status_code, 200)
        locations = json.loads(response.content)
        self.failUnlessEqual(locations, {
            'Uganda': uganda.id,
            'Uganda something else': uganda_duplicate.id,
        })


    def test_get_district_location_with_specified_parent_tree(self):
        uganda = Location.objects.create(name="Uganda")
        uganda_region = Location.objects.create(name="Uganda Region", tree_parent=uganda)
        other_location_that_is_not_child_of_uganda = Location.objects.create(name="Uganda Something else")
        response = self.client.get("/investigators/locations?parent=" + str(uganda.id))
        self.failUnlessEqual(response.status_code, 200)
        locations = json.loads(response.content)
        self.failUnlessEqual(locations, {
            'Uganda Region': uganda_region.id,
        })

    def test_get_location_failures(self):
        response = self.client.get('/investigators/locations')
        self.failUnlessEqual(response.status_code, 200)
        locations = json.loads(response.content)
        self.failUnlessEqual(locations, {})

    def test_create_investigators_success(self):
        country = LocationType.objects.create(name='country', slug='country')
        uganda = Location.objects.create(name="Uganda", type=country)
        backend = Backend.objects.create(name='something')
        form_data = {
            'name': 'Rajini',
            'mobile_number': '987654321',
            'male': 'f',
            'age': '20',
            'level_of_education': 'Nursery',
            'language': 'Luganda',
            'country': uganda.id,
            'location': uganda.id,
            'backend': backend.id,
            'confirm_mobile_number': '987654321',
        }
        investigator = Investigator.objects.filter(name=form_data['name'], backend = Backend.objects.create(name='something1'))
        self.failIf(investigator)
        response = self.client.post('/investigators/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 302) # ensure redirection to list investigator page
        investigator = Investigator.objects.get(name=form_data['name'])
        self.failUnless(investigator.id)
        for key in ['name', 'mobile_number', 'age', 'level_of_education', 'language']:
            value = getattr(investigator, key)
            self.assertEqual(form_data[key], str(value))

        self.assertTrue(investigator.male)
        self.assertEqual(investigator.location, uganda)
        self.assertEqual(len(investigator.households.all()), 0)

    @patch('django.contrib.messages.error')
    def test_create_investigators_failure(self, mock_messages_error):
        country = LocationType.objects.create(name='country', slug='country')
        uganda = Location.objects.create(name="Uganda", type=country)
        backend = Backend.objects.create(name='something')
        form_data = {
            'name': 'Rajini',
            'mobile_number': '987654321',
            'male': 'f',
            'age': '20',
            'level_of_education': 'Nursery',
            'language': 'Luganda',
            'country': uganda.id,
            'location': uganda.id,
            'backend': backend.id,
            'confirm_mobile_number': '987654321',
        }
        investigator = Investigator.objects.filter(name=form_data['name'], backend = Backend.objects.create(name='something1'))
        self.failIf(investigator)

        form_data['location']='Not A Number'
        response = self.client.post('/investigators/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 200)
        investigator = Investigator.objects.filter(name=form_data['name'])
        assert mock_messages_error.called

        form_data['location']=uganda.id
        form_data['confirm_mobile_number']='123456789' # not the same as mobile number, causing non-field error
        response = self.client.post('/investigators/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 200) # ensure redirection to list investigator page
        investigator = Investigator.objects.filter(name=form_data['name'])
        self.failIf(investigator)
        assert mock_messages_error.called
        self.failIf(investigator)

    def test_list_investigators(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=uganda, backend = Backend.objects.create(name='something'))
        response = self.client.get("/investigators/")
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)

        self.assertEqual(len(response.context['investigators']), 1)
        self.assertIn(investigator, response.context['investigators'])
        self.assertNotEqual(None, response.context['request'])

        locations = response.context['location_data'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

    @patch('django.contrib.messages.error')
    def test_list_investigators_no_investigators(self, mock_error_message):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        uganda = Location.objects.create(name="Uganda", type=country)
        investigator = Investigator.objects.filter(location=uganda).delete()
        response = self.client.get("/investigators/")
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)

        self.assertEqual(len(response.context['investigators']), 0)

        locations = response.context['location_data'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

        assert mock_error_message.called_once_with('There are  no investigators currently registered  for this location.')

    def test_filter_list_investigators(self):
        country = LocationType.objects.create(name="country", slug=slugify("country"))
        district = LocationType.objects.create(name="district", slug=slugify("district"))

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto = Location.objects.create(name="Bukoto", tree_parent=kampala)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=uganda, backend = Backend.objects.create(name='something1'))
        investigator2 = Investigator.objects.create(name="Investigator", mobile_number="987654322", location=kampala, backend = Backend.objects.create(name='something2'))
        investigator3 = Investigator.objects.create(name="Investigator", mobile_number="987654323", location=bukoto, backend = Backend.objects.create(name='something3'))

        response = self.client.get("/investigators/?location=" + str(uganda.id))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/index.html', templates)

        self.assertEqual(len(response.context['investigators']), 3)
        for investigator in [investigator1, investigator2, investigator3]:
            self.assertIn(investigator, response.context['investigators'])

        locations = response.context['location_data'].get_widget_data()
        self.assertEquals(len(locations['country']), 1)
        self.assertEquals(locations['country'][0], uganda)

        self.assertEquals(len(locations['district']), 1)
        self.assertEquals(locations['district'][0], kampala)

    def test_check_mobile_number(self):
        investigator = Investigator.objects.create(name="investigator", mobile_number="123456789", backend = Backend.objects.create(name='something'))
        response = self.client.get("/investigators/check_mobile_number?mobile_number=0987654321")
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)

        response = self.client.get("/investigators/check_mobile_number?mobile_number=" + investigator.mobile_number)
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/investigators/new/')
        self.assert_restricted_permission_for('/investigators/')


class ViewInvestigatorDetailsPage(InvestigatorTest):
    def test_view_page(self):
        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        city = LocationType.objects.create(name="City", slug=slugify("city"))
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=city, tree_parent=uganda)
        investigator = Investigator.objects.create(name="investigator", mobile_number="123456789", backend = Backend.objects.create(name='something'), location=kampala)
        response = self.client.get('/investigators/' + str(investigator.pk) + '/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/show.html', templates)
        self.assertEquals(response.context['investigator'], investigator)
        self.assert_restricted_permission_for('/investigators/' + str(investigator.id) +'/')
        
class EditInvestigatorPage(InvestigatorTest):

    def test_edit(self):
        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        city = LocationType.objects.create(name="City", slug=slugify("city"))
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=city, tree_parent=uganda)
        investigator = Investigator.objects.create(name="investigator", mobile_number="123456789", backend = Backend.objects.create(name='something'), location=kampala)
        response = self.client.get('/investigators/' + str(investigator.id) + '/edit/')
        self.assertEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('investigators/investigator_form.html', templates)
        self.assertEquals(response.context['action'], '/investigators/' + str(investigator.id) + '/edit/')
        self.assertEquals(response.context['title'], 'Edit Investigator')
        self.assertEquals(response.context['id'], 'edit-investigator-form')
        self.assertEquals(response.context['button_label'], 'Save')
        self.assertEquals(response.context['loading_text'], 'Saving...')
        self.assertEquals(response.context['country_phone_code'], COUNTRY_PHONE_CODE)
        self.assertIsInstance(response.context['form'], InvestigatorForm)
        locations = response.context['locations'].get_widget_data()
        self.assertEqual(len(locations),2)
        self.assert_restricted_permission_for('/investigators/' + str(investigator.id) +'/edit/')

    def test_edit_post(self):
        country = LocationType.objects.create(name='country', slug='country')
        uganda = Location.objects.create(name="Uganda", type=country)
        backend = Backend.objects.create(name='something')
        data = {
            'name': 'Rajni',
            'mobile_number': '123456789',
            'male': False,
            'age': '20',
            'level_of_education': 'Nursery',
            'language': 'Luganda',
            'location': uganda,
            'backend': backend,
            }
        investigator = Investigator.objects.create(**data)
        form_data={
            'name': 'Rajnikant',
            'mobile_number': investigator.mobile_number,
            'male': True,
            'age': '23',
            'level_of_education': 'Primary',
            'language': 'Luganda',
            'location': uganda.id,
            'backend': backend.id,
            'confirm_mobile_number': investigator.mobile_number
        }
        response = self.client.post('/investigators/%s/edit/' % investigator.id, data=form_data)
        self.failUnlessEqual(response.status_code, 302)
        investigator = Investigator.objects.get(name=form_data['name'])
        self.failUnless(investigator.id)
        for key in ['name', 'mobile_number', 'age', 'level_of_education', 'language']:
            value = getattr(investigator, key)
            self.assertEqual(form_data[key], str(value))

        self.assertTrue(investigator.male)
        self.assertEqual(investigator.location, uganda)
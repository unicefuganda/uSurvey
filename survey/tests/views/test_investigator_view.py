import json

from django.test.client import Client
from mock import *
from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models.locations import *
from django.contrib.auth.models import User
# from survey.interviewer_configs import COUNTRY_PHONE_CODE
from django.conf import settings
from survey.models import Backend, Household, LocationTypeDetails, EnumerationArea
from survey.models.interviewer import Interviewer

from survey.tests.base_test import BaseTest

from survey.forms.interviewer import InterviewerForm
from survey.models.formula import *

#Eswar getting http 302 error for /interviewers/new/
class InvestigatorsViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_investigators')
        self.client.login(username='Rajni', password='I_Rock')

        self.country = LocationType.objects.create(name='Country', slug='country')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.city = LocationType.objects.create(name='City', slug='city')
        self.village = LocationType.objects.create(name='Village', slug='village')

        self.uganda = Location.objects.create(name='Uganda', type=self.country)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.country)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.district)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.city)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.village)

        self.kampala = Location.objects.create(name='Kampala', tree_parent=self.uganda, type=self.district)
        self.abim = Location.objects.create(name='Abim', tree_parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)

    # def test_new(self):
    #     ea = EnumerationArea.objects.create(name="EA2")
    #     ea.locations.add(self.uganda)
    #     backend = Backend.objects.create(name='something')
    #     form_data = {
    #         'name': 'Rajini',
    #         'male': 'f',
    #         'age': '20',
    #         'level_of_education': 'Nursery',
    #         'language': 'Luganda',
    #         'country': self.uganda.id,
    #         'ea': ea.id,
    #         'backend': backend.id,
    #         'confirm_mobile_number': '987654321',
    #     }
    #     response = self.client.post('/interviewers/new/', data=form_data)
    #     self.failUnlessEqual(response.status_code, 200)
    #     templates = [template.name for template in response.templates]
    #     self.assertIn('investigators/investigator_form.html', templates)
    #     self.assertEquals(response.context['action'], '/investigators/new/')
    #     self.assertEquals(response.context['country_phone_code'], COUNTRY_PHONE_CODE)
    #     self.assertEquals(response.context['title'], 'New Investigator')
    #     self.assertEquals(response.context['id'], 'create-investigator-form')
    #     self.assertEquals(response.context['button_label'], 'Create')
    #     self.assertEquals(response.context['loading_text'], 'Creating...')
    #
    #     locations = response.context['locations'].get_widget_data()
    #     self.assertEquals(len(locations.keys()), 2)
    #     self.assertEquals(locations.keys()[0], 'district')
    #     self.assertEquals(len(locations['district']), 2)
    #     self.assertEquals(locations['district'][1], self.kampala)
    #     self.assertEquals(locations['district'][0], self.abim)
    #
    #     self.assertEquals(len(locations['city']), 0)

    #Eswar not required
    # def test_get_district_location_returns_all_locations_if_parent_not_specified(self):
    #     uganda_duplicate = Location.objects.create(name="Uganda something else")
    #     response = self.client.get('/investigators/locations')
    #     self.failUnlessEqual(response.status_code, 200)
    #     locations = json.loads(response.content)
    #     self.failUnlessEqual(locations, {
    #         'Uganda': self.uganda.id,
    #         'Uganda something else': uganda_duplicate.id,
    #     })

    # def test_get_district_location_returns_all_locations_if_parent_empty(self):
    #     uganda_duplicate = Location.objects.create(name="Uganda something else")
    #     response = self.client.get('/investigators/locations?parent=')
    #     self.failUnlessEqual(response.status_code, 200)
    #     locations = json.loads(response.content)
    #     self.failUnlessEqual(locations, {
    #         'Uganda': self.uganda.id,
    #         'Uganda something else': uganda_duplicate.id,
    #     })

#     def test_get_district_location_with_specified_parent_tree(self):
#         response = self.client.get("/investigators/locations?parent=" + str(self.uganda.id))
#         self.failUnlessEqual(response.status_code, 200)
#         locations = json.loads(response.content)
#         self.failUnlessEqual(locations, {'Abim': self.abim.id, 'Kampala': self.kampala.id,})
#
#     def test_get_location_failures(self):
#         Location.objects.all().delete()
#         response = self.client.get('/investigators/locations')
#         self.failUnlessEqual(response.status_code, 200)
#         locations = json.loads(response.content)
#         self.failUnlessEqual(locations, {})
#
    # def test_interviewer_list(self):
    #     print "R"
    #     response = self.client.get('/interviewers/')
    #     self.assertEqual(response.status_code,200)

    def test_create_investigators_success(self):
        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(self.uganda)

        # investigator = Interviewer.objects.create(name="Investigator",
        #                                            ea=self.ea,
        #                                            gender='1',level_of_education='Primary',
        #                                            language='Eglish',weights=0, date_of_birth=date(1988,10,9))
        backend = Backend.objects.create(name='something')
        form_data = {
            'name': 'Rajini',
            'male': 'f',
            'age': '20',
            'level_of_education': 'Nursery',
            'language': 'Luganda',
            'country': self.uganda.id,
            'ea': ea.id,
            'backend': backend.id,
            'confirm_mobile_number': '987654321',
        }
        investigator = Interviewer.objects.filter(name=form_data['name'], ea=ea,
                                                   )
        self.failIf(investigator)
        response = self.client.post('/interviewers/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 302) # ensure redirection to list investigator page
        # investigator = Interviewer.objects.get(name=form_data['name'])
        # self.failUnless(investigator.id)
        # for key in ['name', 'mobile_number', 'age', 'level_of_education', 'language']:
        #     value = getattr(investigator, key)
        #     self.assertEqual(form_data[key], str(value))
        #
        # self.assertTrue(investigator.male)
        # self.assertEqual(investigator.location, self.uganda)
        # self.assertEqual(len(investigator.households.all()), 0)
        # self.assertRedirects(response, '/investigators/', 302, 200)

    def test_downlaod_interviewer(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        #ea.locations.add(kampala)
        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        response = self.client.post('/interviewers/export/')

#     @patch('django.contrib.messages.error')
#     def test_create_investigators_failure(self, mock_messages_error):
#         backend = Backend.objects.create(name='something')
#         form_data = {
#             'name': 'Rajini',
#             'mobile_number': '987654321',
#             'male': 'f',
#             'age': '20',
#             'level_of_education': 'Nursery',
#             'language': 'Luganda',
#             'country': self.uganda.id,
#             'location': self.kampala.id,
#             'backend': backend.id,
#             'confirm_mobile_number': '987654321',
#         }
#         investigator = Investigator.objects.filter(name=form_data['name'], backend = Backend.objects.create(name='something1'))
#         self.failIf(investigator)
#
#         form_data['location']='Not A Number'
#         response = self.client.post('/investigators/new/', data=form_data)
#         self.failUnlessEqual(response.status_code, 200)
#         investigator = Investigator.objects.filter(name=form_data['name'])
#         assert mock_messages_error.called
#
#         form_data['location']=self.kampala.id
#         form_data['confirm_mobile_number']='123456789' # not the same as mobile number, causing non-field error
#         response = self.client.post('/investigators/new/', data=form_data)
#         self.failUnlessEqual(response.status_code, 200) # ensure redirection to list investigator page
#         investigator = Investigator.objects.filter(name=form_data['name'])
#         self.failIf(investigator)
#         assert mock_messages_error.called
#         self.failIf(investigator)
#
#     def test_list_investigators(self):
#         investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=self.kampala,
#                                                    backend = Backend.objects.create(name='something'))
#         response = self.client.get("/investigators/")
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/index.html', templates)
#
#         self.assertEqual(len(response.context['investigators']), 1)
#         self.assertIn(investigator, response.context['investigators'])
#         self.assertNotEqual(None, response.context['request'])
#
#         locations = response.context['location_data'].get_widget_data()
#         self.assertEquals(len(locations['district']), 2)
#         self.assertIn(self.kampala, locations['district'])
#         self.assertIn(self.abim, locations['district'])
#
#     @patch('django.contrib.messages.error')
#     def test_list_investigators_no_investigators(self, mock_error_message):
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(self.kampala)
#
#         investigator = Investigator.objects.filter(ea=ea).delete()
#         response = self.client.get("/investigators/")
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/index.html', templates)
#
#         self.assertEqual(len(response.context['investigators']), 0)
#
#         assert mock_error_message.called_once_with('There are  no investigators currently registered  for this location.')
#
#     def test_filter_list_investigators_by_location(self):
#         bukoto = Location.objects.create(name="Bukoto", tree_parent=self.kampala_city, type=self.village)
#
#         kampala_city_ea = EnumerationArea.objects.create(name="EA2")
#         kampala_city_ea.locations.add(self.kampala_city)
#         kampala_ea = EnumerationArea.objects.create(name="EA3")
#         kampala_ea.locations.add(self.kampala)
#         bukoto_ea = EnumerationArea.objects.create(name="EA2")
#         bukoto_ea.locations.add(bukoto)
#
#         investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654322", ea=kampala_ea,
#                                                     backend=Backend.objects.create(name='something2'))
#         investigator2 = Investigator.objects.create(name="Investigator", mobile_number="987654321", ea=kampala_city_ea,
#                                                     backend=Backend.objects.create(name='something1'))
#         investigator3 = Investigator.objects.create(name="Investigator", mobile_number="987654323", ea=bukoto_ea,
#                                                     backend=Backend.objects.create(name='something3'))
#
#         response = self.client.get("/investigators/?location=" + str(self.kampala.id))
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/index.html', templates)
#
#         self.assertEqual(len(response.context['investigators']), 3)
#         for investigator in [investigator1, investigator2, investigator3]:
#             self.assertIn(investigator, response.context['investigators'])
#
#         response = self.client.get("/investigators/?location=" + str(self.kampala_city.id))
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/index.html', templates)
#
#         self.assertEqual(len(response.context['investigators']), 2)
#         for investigator in [investigator2, investigator3]:
#             self.assertIn(investigator, response.context['investigators'])
#
#         response = self.client.get("/investigators/?location=" + str(bukoto.id))
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/index.html', templates)
#
#         self.assertEqual(len(response.context['investigators']), 1)
#         self.assertEqual(investigator3, response.context['investigators'][0])
#
#     def test_filter_list_investigators_by_ea(self):
#         bukoto = Location.objects.create(name="Bukoto", tree_parent=self.kampala_city, type=self.village)
#
#         subvillage = LocationType.objects.create(name='Sub Village', slug='subvillage')
#         LocationTypeDetails.objects.create(country=self.uganda, location_type=subvillage)
#
#
#         kampala_city_ea = EnumerationArea.objects.create(name="EA2")
#         kampala_city_ea.locations.add(self.kampala_city)
#         kampala_ea = EnumerationArea.objects.create(name="EA3")
#         kampala_ea.locations.add(self.kampala)
#         bukoto_ea = EnumerationArea.objects.create(name="EA2")
#         bukoto_ea.locations.add(bukoto)
#
#         investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654322", ea=kampala_ea,
#                                                     backend=Backend.objects.create(name='something2'))
#         investigator2 = Investigator.objects.create(name="Investigator", mobile_number="987654321", ea=kampala_city_ea,
#                                                     backend=Backend.objects.create(name='something1'))
#         investigator3 = Investigator.objects.create(name="Investigator", mobile_number="987654323", ea=bukoto_ea,
#                                                     backend=Backend.objects.create(name='something3'))
#
#         response = self.client.get("/investigators/?ea=" + str(kampala_ea.id))
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/index.html', templates)
#
#         self.assertEqual(len(response.context['investigators']), 1)
#         self.assertEqual(investigator1, response.context['investigators'][0])
#
#         response = self.client.get("/investigators/?ea=" + str(kampala_city_ea.id))
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/index.html', templates)
#
#         self.assertEqual(len(response.context['investigators']), 1)
#         self.assertEqual(investigator2, response.context['investigators'][0])
#
#         response = self.client.get("/investigators/?ea=" + str(bukoto_ea.id))
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/index.html', templates)
#
#         self.assertEqual(len(response.context['investigators']), 1)
#         self.assertEqual(investigator3, response.context['investigators'][0])
#
#     def test_check_mobile_number(self):
#         investigator = Investigator.objects.create(name="investigator", mobile_number="123456789", backend = Backend.objects.create(name='something'))
#         response = self.client.get("/investigators/check_mobile_number?mobile_number=0987654321")
#         self.failUnlessEqual(response.status_code, 200)
#         json_response = json.loads(response.content)
#         self.assertTrue(json_response)
#
#         response = self.client.get("/investigators/check_mobile_number?mobile_number=" + investigator.mobile_number)
#         self.failUnlessEqual(response.status_code, 200)
#         json_response = json.loads(response.content)
#         self.assertFalse(json_response)
#
#     def test_restricted_permssion(self):
#         self.assert_restricted_permission_for('/investigators/new/')
#         self.assert_restricted_permission_for('/investigators/')
#
#
# class ViewInvestigatorDetailsPage(BaseTest):
#     def setUp(self):
#         self.client = Client()
#         user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
#         raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_investigators')
#         self.client.login(username='Rajni', password='I_Rock')
#
#     def test_view_page(self):
#         country = LocationType.objects.create(name="Country", slug=slugify("country"))
#         city = LocationType.objects.create(name="City", slug=slugify("city"))
#         uganda = Location.objects.create(name="Uganda", type=country)
#         kampala = Location.objects.create(name="Kampala", type=city, tree_parent=uganda)
#         ea_kampala = EnumerationArea.objects.create(name="ea_kampala")
#         ea_kampala.locations.add(kampala)
#         investigator = Investigator.objects.create(name="investigator", mobile_number="123456789",
#                                                    backend=Backend.objects.create(name='something'), ea=ea_kampala)
#         response = self.client.get('/investigators/' + str(investigator.pk) + '/')
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/show.html', templates)
#         self.assertEquals(response.context['investigator'], investigator)
#         self.assertEquals(response.context['cancel_url'], '/investigators/')
#         self.assert_restricted_permission_for('/investigators/' + str(investigator.id) +'/')
#
#
# class EditInvestigatorPage(BaseTest):
#     def setUp(self):
#         self.client = Client()
#         user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
#         raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_investigators')
#         self.client.login(username='Rajni', password='I_Rock')
#
#     def test_edit(self):
#         country = LocationType.objects.create(name="Country", slug=slugify("country"))
#         city = LocationType.objects.create(name="City", slug=slugify("city"))
#         village = LocationType.objects.create(name="Village", slug=slugify("village"))
#
#         uganda = Location.objects.create(name="Uganda", type=country)
#         LocationTypeDetails.objects.create(country=uganda, location_type=country)
#         LocationTypeDetails.objects.create(country=uganda, location_type=city)
#         LocationTypeDetails.objects.create(country=uganda, location_type=village)
#
#         kampala = Location.objects.create(name="Kampala", type=city, tree_parent=uganda)
#         bukoto = Location.objects.create(name="Bukoto", type=city, tree_parent=kampala)
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(bukoto)
#
#         investigator = Investigator.objects.create(name="investigator", mobile_number="123456789",
#                                                    backend = Backend.objects.create(name='something'), ea=ea)
#         response = self.client.get('/investigators/' + str(investigator.id) + '/edit/')
#         self.assertEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('investigators/investigator_form.html', templates)
#         self.assertEquals(response.context['action'], '/investigators/' + str(investigator.id) + '/edit/')
#         self.assertEquals(response.context['title'], 'Edit Investigator')
#         self.assertEquals(response.context['id'], 'edit-investigator-form')
#         self.assertEquals(response.context['button_label'], 'Save')
#         self.assertEquals(response.context['loading_text'], 'Saving...')
#         self.assertEquals(response.context['country_phone_code'], COUNTRY_PHONE_CODE)
#         self.assertEquals(response.context['cancel_url'], '/investigators/')
#         self.assertIsInstance(response.context['form'], InvestigatorForm)
#         locations = response.context['locations'].get_widget_data()
#         self.assertEqual(len(locations), 1)
#         self.assert_restricted_permission_for('/investigators/' + str(investigator.id) +'/edit/')
#
#     def test_edit_post(self):
#         country = LocationType.objects.create(name='country', slug='country')
#         uganda = Location.objects.create(name="Uganda", type=country)
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(uganda)
#
#         backend = Backend.objects.create(name='something')
#         data = {
#             'name': 'Rajni',
#             'mobile_number': '123456789',
#             'male': False,
#             'age': '20',
#             'level_of_education': 'Nursery',
#             'language': 'Luganda',
#             'ea': ea,
#             'backend': backend,
#             }
#         investigator = Investigator.objects.create(**data)
#         form_data={
#             'name': 'Rajnikant',
#             'mobile_number': investigator.mobile_number,
#             'male': True,
#             'age': '23',
#             'level_of_education': 'Primary',
#             'language': 'Luganda',
#             'ea': ea.id,
#             'backend': backend.id,
#             'confirm_mobile_number': investigator.mobile_number
#         }
#         response = self.client.post('/investigators/%s/edit/' % investigator.id, data=form_data)
#         self.failUnlessEqual(response.status_code, 302)
#         investigator = Investigator.objects.get(name=form_data['name'])
#         self.failUnless(investigator.id)
#         for key in ['name', 'mobile_number', 'age', 'level_of_education', 'language']:
#             value = getattr(investigator, key)
#             self.assertEqual(form_data[key], str(value))
#
#         self.assertTrue(investigator.male)
#         self.assertEqual(investigator.location, uganda)
#         self.assertRedirects(response, '/investigators/', 302, 200)
#
#
# class BlockInvestigatorTest(BaseTest):
#     def setUp(self):
#         self.client = Client()
#         user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
#         raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_investigators')
#         self.client.login(username='Rajni', password='I_Rock')
#
#         country = LocationType.objects.create(name='country', slug='country')
#         uganda = Location.objects.create(name="Uganda", type=country)
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(uganda)
#
#         backend = Backend.objects.create(name='something')
#         data = {
#             'name': 'Rajni',
#             'mobile_number': '123456789',
#             'male': False,
#             'age': '20',
#             'level_of_education': 'Nursery',
#             'language': 'Luganda',
#             'ea': ea,
#             'backend': backend,
#             }
#         self.investigator = Investigator.objects.create(**data)
#
#     def test_should_know_how_to_block_an_investigator_and_show_block_message(self):
#
#         response = self.client.get('/investigators/%s/block/' % self.investigator.id)
#         updated_investigator = Investigator.objects.get(id=self.investigator.id)
#         success_message = "Investigator successfully blocked."
#
#         self.assertTrue(updated_investigator.is_blocked)
#         self.assertTrue(success_message in response.cookies['messages'].value)
#         self.assertRedirects(response, '/investigators/', 302, 200)
#
#     def test_should_throw_error_message_if_investigator_does_not_exist(self):
#         non_existent_id = 999
#         response = self.client.get('/investigators/%s/block/' % non_existent_id)
#         error_message = "Investigator does not exist."
#
#         self.assertTrue(error_message in response.cookies['messages'].value)
#         self.assertRedirects(response, '/investigators/', 302, 200)
#
#     def test_restricted_permssion(self):
#         self.assert_restricted_permission_for('/investigators/1/block/')
#
#     def test_should_dissociate_all_households_linked_to_investigator_when_blocked(self):
#         household = Household.objects.create(investigator=self.investigator, location=self.investigator.location, uid=0)
#         response = self.client.get('/investigators/%d/block/' % int(self.investigator.id))
#
#         updated_investigator = Investigator.objects.get(id=self.investigator.id)
#         self.assertEqual(0, len(updated_investigator.households.all()))
#
#
# class UnblockInvestigatorTest(BaseTest):
#     def setUp(self):
#         self.client = Client()
#         user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
#         raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_investigators')
#         self.client.login(username='Rajni', password='I_Rock')
#
#         country = LocationType.objects.create(name='country', slug='country')
#         uganda = Location.objects.create(name="Uganda", type=country)
#         backend = Backend.objects.create(name='something')
#         data = {
#             'name': 'Rajni',
#             'mobile_number': '123456789',
#             'male': False,
#             'age': '20',
#             'level_of_education': 'Nursery',
#             'language': 'Luganda',
#             'location': uganda,
#             'backend': backend,
#             'is_blocked': True
#             }
#         self.investigator = Investigator.objects.create(**data)
#
#     def test_should_know_how_to_unblock_an_investigator_and_show_unblock_message(self):
#
#         response = self.client.get('/investigators/%s/unblock/' % self.investigator.id)
#         updated_investigator = Investigator.objects.get(id=self.investigator.id)
#         success_message = "Investigator successfully unblocked."
#
#         self.assertFalse(updated_investigator.is_blocked)
#         self.assertTrue(success_message in response.cookies['messages'].value)
#         self.assertRedirects(response, '/investigators/', 302, 200)
#
#     def test_should_throw_error_message_if_investigator_does_not_exist(self):
#         non_existent_id = 999
#         response = self.client.get('/investigators/%s/unblock/' % non_existent_id)
#         error_message = "Investigator does not exist."
#
#         self.assertTrue(error_message in response.cookies['messages'].value)
#         self.assertRedirects(response, '/investigators/', 302, 200)
#
#     def test_restricted_permssion(self):
#         self.assert_restricted_permission_for('/investigators/1/unblock/')
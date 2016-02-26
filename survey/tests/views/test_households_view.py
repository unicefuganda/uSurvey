import json
from django.template.defaultfilters import slugify
from datetime import date
from django.test.client import Client
from mock import *
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models.locations import *
from survey.models import LocationTypeDetails, EnumerationArea, HouseholdListing
from survey.models.households import HouseholdMember, HouseholdHead, Household
from survey.models.backend import Backend
from survey.models.interviewer import Interviewer

from survey.tests.base_test import BaseTest
from survey.forms.household import *
from survey.views.household import *


class HouseholdViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_households')
        self.client.login(username='Rajni', password='I_Rock')

    def test_new_GET(self):
        response = self.client.get('/households/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('households/new.html', templates)
        self.assertEquals(response.context['action'], '/households/new/')
        self.assertEquals(response.context['id'], 'create-household-form')
        self.assertEquals(response.context['button_label'], 'Save')
        self.assertEquals(response.context['heading'], 'New Household')
        self.assertEquals(response.context['loading_text'], 'Creating...')
        investigator_form = {'value': '', 'text': '', 'options': Interviewer.objects.all(), 'error': ''}
        print response.context.keys(),"+++++++++++++++++++"
        # self.assert_dictionary_equal(response.context['investigator_form'], investigator_form)
        self.assertIsNotNone(response.context['householdform'])
        self.assertIsNotNone(response.context['headform'])
        self.assertIsNotNone(response.context['locations_filter'])

    def test_get_investigators(self):
        country = LocationType.objects.create(name="Country", slug="country")
        uganda = Location.objects.create(name="Uganda", type=country)
        ea = EnumerationArea.objects.create(name="EA1")
        ea.locations.add(uganda)
        ea_2 = EnumerationArea.objects.create(name="EA2")
        ea_2.locations.add(uganda)

        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        Interviewer.objects.create(name="Investigator1",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)

        response = self.client.get('/households/interviewers?ea=' + str(ea.id))
        self.failUnlessEqual(response.status_code, 200)
        result_investigator = json.loads(response.content)
        self.failUnlessEqual(result_investigator, {u'Investigator1': 2, u'Investigator': 1})

    def test_gets_only_investigators_who_are_not_blocked(self):
        country = LocationType.objects.create(name="Country", slug="country")
        uganda = Location.objects.create(name="Uganda", type=country)
        backend = Backend.objects.create(name='something')
        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(uganda)

        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        blocked_investigator = Interviewer.objects.create(name="Investigator1",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0,is_blocked=True)
        response = self.client.get('/households/interviewers?ea=' + str(ea.id))
        self.failUnlessEqual(response.status_code, 200)
        result_investigator = json.loads(response.content)
        self.failUnlessEqual(result_investigator, {u'Investigator': 1})

    def test_get_investigators_returns_investigators_with_no_location_if_location_empty(self):
        country = LocationType.objects.create(name="Country", slug="country")
        uganda = Location.objects.create(name="Uganda", type=country)
        backend = Backend.objects.create(name='something')
        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(uganda)

        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        investigator_duplicate = Interviewer.objects.create(name="Investigator1",

                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        response = self.client.get('/households/interviewers?locations=')
        self.failUnlessEqual(response.status_code, 200)
        result_investigator = json.loads(response.content)
        self.failUnlessEqual(result_investigator, {u'Investigator1': 2})

    def test_get_investigators_failures(self):
        response = self.client.get('/households/interviewers')
        self.failUnlessEqual(response.status_code, 200)
        result_investigator = json.loads(response.content)
        self.failUnlessEqual(result_investigator, {})

#    Eswar Tony to confirm on validate_investigator
#     def test_validate_investigators(self):
#         country = LocationType.objects.create(name="Country", slug="country")
#         uganda = Location.objects.create(name="Uganda", type=country)
#         backend = Backend.objects.create(name='something')
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(uganda)
#
#         investigator = Interviewer.objects.create(name="Investigator",
#                                                    ea=ea,
#                                                    gender='1',level_of_education='Primary',
#                                                    language='Eglish',weights=0)
#         householdForm = HouseholdForm()
#         posted_locations = [uganda]
#         request = MagicMock()
#         request.POST = {'investigator': investigator.id}
#
#         investigator_result, investigator_form = validate_investigator(request, householdForm, ea)
#
#         self.assertEquals(investigator_result, investigator)
#         self.assertEquals(investigator_form['value'], investigator.id)
#         self.assertEquals(investigator_form['text'], 'inv')
#         self.assertEquals(investigator_form['error'], '')
#         self.assertEquals(len(investigator_form['options']), 1)
#         self.assertEquals(investigator_form['options'][0], investigator)

#     @patch('django.forms.util.ErrorList')
#     @patch('survey.models.Investigator.objects.get')
#     def test_validate_investigators_no_investigator_posted(self, mock_investigator_get, mock_error_class):
#         uganda = Location.objects.create(name="Uganda")
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(uganda)
#
#         investigator = Investigator.objects.create(name="inv", mobile_number='987654321', ea=ea,
#                                                    backend=Backend.objects.create(name='something'))
#         householdForm = HouseholdForm()
#         posted_locations = [uganda]
#         request = MagicMock()
#         request.POST = {'investigator': investigator.id}
#         mock_investigator_get.side_effect = MultiValueDictKeyError
#
#         investigator_result, investigator_form = validate_investigator(request, householdForm, ea)
#
#         self.assertEquals(investigator_result, None)
#         self.assertEquals(investigator_form['value'], '')
#         self.assertEquals(investigator_form['text'], '')
#         message = "No investigator provided."
#         self.assertEquals(investigator_form['error'], message)
#         self.assertEquals(len(investigator_form['options']), 1)
#         self.assertEquals(investigator_form['options'][0], investigator)
#         assert mock_error_class.called_once_with([message])
#
#     @patch('django.forms.util.ErrorList')
#     @patch('survey.models.Investigator.objects.get')
#     def test_validate_investigators_non_existing_investigator_id_posted(self, mock_investigator_get, mock_error_class):
#         uganda = Location.objects.create(name="Uganda")
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(uganda)
#
#         investigator = Investigator.objects.create(name="inv", mobile_number='987654321', ea=ea,
#                                                    backend=Backend.objects.create(name='something'))
#         householdForm = HouseholdForm()
#         request = MagicMock()
#         request.POST = {'investigator': 'mocked so not important'}
#         mock_investigator_get.side_effect = ObjectDoesNotExist
#
#         investigator_result, investigator_form = validate_investigator(request, householdForm, ea)
#
#         self.assertEquals(investigator_result, None)
#         self.assertEquals(investigator_form['value'], 'mocked so not important')
#         self.assertEquals(investigator_form['text'], 'mocked so not important')
#         message = "You provided an unregistered investigator."
#         self.assertEquals(investigator_form['error'], message)
#         self.assertEquals(len(investigator_form['options']), 1)
#         self.assertEquals(investigator_form['options'][0], investigator)
#         assert mock_error_class.called_once_with([message])
#
#     @patch('django.forms.util.ErrorList')
#     @patch('survey.models.Investigator.objects.get')
#     def test_validate_investigators_NAN_investigator_id_posted(self, mock_investigator_get, mock_error_class):
#         uganda = Location.objects.create(name="Uganda")
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(uganda)
#
#         investigator = Investigator.objects.create(name="inv", mobile_number='987654321', ea=ea,
#                                                    backend=Backend.objects.create(name='something'))
#         householdForm = HouseholdForm()
#         posted_locations = [uganda]
#         request = MagicMock()
#         request.POST = {'investigator': 'mocked so not important'}
#         mock_investigator_get.side_effect = ValueError
#
#         investigator_result, investigator_form = validate_investigator(request, householdForm, ea)
#
#         self.assertEquals(investigator_result, None)
#         self.assertEquals(investigator_form['value'], 'mocked so not important')
#         self.assertEquals(investigator_form['text'], 'mocked so not important')
#         message = "You provided an unregistered investigator."
#         self.assertEquals(investigator_form['error'], message)
#         self.assertEquals(len(investigator_form['options']), 1)
#         self.assertEquals(investigator_form['options'][0], investigator)
#         assert mock_error_class.called_once_with([message])

#   Eswar ned to check after reaching office
#     def test_create_households(self):
#         country = LocationType.objects.create(name='country', slug='country')
#         district = LocationType.objects.create(name='district', slug='district', parent=country)
#         uganda = Location.objects.create(name="Uganda", type=country)
#         # burundi = Location.objects.create(name="Burundi", type=country)
#         dist = Location.objects.create(name="dist", type=district, parent=uganda)
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(uganda)
#         survey = Survey.objects.create(name="Survey A", description="open survey", has_sampling=True)
#         investigator = Interviewer.objects.create(name="Investigator",
#                                                    ea=ea,
#                                                    gender='1',level_of_education='Primary',
#                                                    language='Eglish',weights=0)
#         household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=investigator,initial_survey=survey)
#         household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
#                                              last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",
#                                              head_sex='MALE')
#         survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=survey)
#         SurveyAllocation.objects.create(interviewer=investigator,survey=survey,allocation_ea=ea,stage=1,status=0)
#         form_data = {
#             'surname': 'Rajini',
#             'first_name': 'Kant',
#             'gender': 1,
#             'date_of_birth': '19-10-1980',
#             'household':household.id,
#             'survey_listing':survey_householdlisting.id,
#             'registrar': investigator.id,
#             'registration_channel':'ODK Access',
#             'occupation': 'Student',
#             'level_of_education': 'Nursery',
#             'resident_since': '19-10-2001',
#         }
#
#         hHead = HouseholdHead.objects.filter(surname=form_data['surname'])
#         household = Household.objects.filter(house_number=123456)
#         self.failIf(hHead)
#         # self.trueIf(household)
#         response = self.client.post('/households/new/', data=form_data)
#         self.failUnlessEqual(response.status_code, 200) # ensure redirection to list investigator page
#         print HouseholdHead.objects.all()
#         hHead = HouseholdHead.objects.get(surname=form_data['surname'])
#         # household = Household.objects.get(uid=form_data['house_number'])
#         print household
#         self.failUnless(hHead.id)
#         self.failUnless(household.id)
#         for key in ['surname', 'first_name', 'date_of_birth', 'occupation',
#                     'level_of_education', 'resident_since_year', 'resident_since_month']:
#             value = getattr(hHead, key)
#             self.assertEqual(str(form_data[key]), str(value))
#
#         self.assertEqual(hHead.male, False)
#         # self.assertEqual(household.investigator, investigator)
#         # self.assertEqual(household.location, investigator.location)
#         # self.assertEqual(household.household_code, household_code)
#         self.assertEqual(hHead.household, household)
#
#         investigator.ea = ea
#         investigator.save()
#         self.assertEqual(household.location, uganda)

#     def test_create_households_unsuccessful(self):
#         country = LocationType.objects.create(name='country', slug='country')
#         district = LocationType.objects.create(name='district', slug='district')
#         uganda = Location.objects.create(name="Uganda", type=country)
#         LocationTypeDetails.objects.create(country=uganda, location_type=country)
#         LocationTypeDetails.objects.create(country=uganda, location_type=district)
#
#         kampala = Location.objects.create(name="kampala", type=district, tree_parent=uganda)
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(kampala)
#
#         investigator = Investigator.objects.create(name="inv", mobile_number='987654321', ea=ea,
#                                                    backend=Backend.objects.create(name='something'))
#         form_data = {
#             'ea': ea.id,
#             'investigator': investigator.id,
#             'surname': 'Rajini',
#             'first_name': 'Kant',
#             'male': 'False',
#             'age': '20',
#             'occupation': 'Student',
#             'level_of_education': 'Nursery',
#             'resident_since_year': '2013',
#             'resident_since_month': '5',
#             'time_measure': 'Years',
#             'uid': '2',
#         }
#         hHead = HouseholdHead.objects.filter(surname=form_data['surname'])
#         household = Household.objects.filter(uid=form_data['uid'])
#         self.failIf(hHead)
#         self.failIf(household)
#
#         form_with_invalid_data = form_data
#         form_with_invalid_data['age'] = -20
#
#         response = self.client.post('/households/new/', data=form_with_invalid_data)
#         self.failUnlessEqual(response.status_code, 200)
#         self.assertEquals(response.context['selected_location'], kampala)
#
#         hHead = HouseholdHead.objects.filter(surname=form_data['surname'])
#         household = Household.objects.filter(uid=form_data['uid'])
#         self.failIf(hHead)
#         self.failIf(household)
#
#     def test_create_households_unsuccessful_with_non_field_errors(self):
#
#         country = LocationType.objects.create(name='country', slug='country')
#         district = LocationType.objects.create(name='district', slug='district')
#         uganda = Location.objects.create(name="Uganda", type=country)
#         LocationTypeDetails.objects.create(country=uganda, location_type=country)
#         LocationTypeDetails.objects.create(country=uganda, location_type=district)
#
#         kampala = Location.objects.create(name="kampala", type=district, tree_parent=uganda)
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(kampala)
#
#         form_data = {
#             'ea': ea.id,
#             'surname': 'Rajini',
#             'first_name': 'Kant',
#             'male': 'False',
#             'occupation': 'Student',
#             'level_of_education': 'Nursery',
#             'resident_since_year': '2013',
#             'resident_since_month': '5',
#             'time_measure': 'Years',
#             'uid': '2',
#         }
#
#         form_with_invalid_data = form_data
#         form_with_invalid_data['surname'] = ''
#
#         response = self.client.post('/households/new/', data=form_with_invalid_data)
#         self.failUnlessEqual(response.status_code, 200)
#         self.assertIsNotNone(response.context['householdform'].get('household').non_field_errors())
#         [self.assertIn(str(err), str(response)) for err in response.context['householdform'].get('household').non_field_errors()]
#
#     def test_restricted_permssion(self):
#         self.assert_restricted_permission_for('/households/new/')
#
#     def test_listing_households(self):
#         country = LocationType.objects.create(name="country", slug=slugify("country"))
#         uganda = Location.objects.create(name="Uganda", type=country)
#         district = LocationType.objects.create(name='district', slug='district')
#         village = LocationType.objects.create(name='village', slug='village')
#         LocationTypeDetails.objects.create(country=uganda, location_type=country)
#         LocationTypeDetails.objects.create(country=uganda, location_type=district)
#         LocationTypeDetails.objects.create(country=uganda, location_type=village)
#
#         kampala = Location.objects.create(name="kampala", type=district, tree_parent=uganda)
#
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(kampala)
#
#         investigator = Investigator.objects.create(name="inv", mobile_number='987654321', ea=ea,
#                                                    backend=Backend.objects.create(name='something'))
#         household_a = Household.objects.create(investigator=investigator, ea=investigator.ea, uid=0)
#         household_b = Household.objects.create(investigator=investigator, ea=investigator.ea, uid=1)
#         household_c = Household.objects.create(investigator=investigator, ea=investigator.ea, uid=2)
#
#         HouseholdHead.objects.create(surname='Bravo', household=household_b, date_of_birth='1980-09-01')
#         HouseholdHead.objects.create(surname='Alpha', household=household_a, date_of_birth='1980-09-01')
#         HouseholdHead.objects.create(surname='Charlie', household=household_c, date_of_birth='1980-09-01')
#         response = self.client.get('/households/')
#
#         self.assertEqual(response.status_code, 200)
#
#         templates = [template.name for template in response.templates]
#
#         self.assertIn('households/index.html', templates)
#         self.assertEqual(len(response.context['households']), 3)
#         self.assertEqual(household_a, response.context['households'][0])
#         self.assertEqual(household_b, response.context['households'][1])
#         self.assertEqual(household_c, response.context['households'][2])
#
#         locations = response.context['location_data'].get_widget_data()
#         self.assertEquals(len(locations['district']), 1)
#         self.assertEquals(locations['district'][0], kampala)
#
#     def test_should_render_without_duplicates_at_the_end_households_without_heads_with_or_without_members(self):
#         country = LocationType.objects.create(name="country", slug=slugify("country"))
#         uganda = Location.objects.create(name="Uganda", type=country)
#         district = LocationType.objects.create(name='district', slug='district')
#         village = LocationType.objects.create(name='village', slug='village')
#         LocationTypeDetails.objects.create(country=uganda, location_type=country)
#         LocationTypeDetails.objects.create(country=uganda, location_type=district)
#         LocationTypeDetails.objects.create(country=uganda, location_type=village)
#
#         kampala = Location.objects.create(name="kampala", type=district, tree_parent=uganda)
#
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(kampala)
#
#         investigator = Investigator.objects.create(name="inv", mobile_number='987654321', ea=ea,
#                                                    backend=Backend.objects.create(name='something'))
#         household_a = Household.objects.create(investigator=investigator, ea=investigator.ea, uid=0)
#         household_b = Household.objects.create(investigator=investigator, ea=investigator.ea, uid=1)
#         household_c = Household.objects.create(investigator=investigator, ea=investigator.ea, uid=2)
#
#         HouseholdHead.objects.create(surname='Bravo', household=household_b, date_of_birth='1980-09-01')
#         HouseholdMember.objects.create(surname='A', household=household_a, date_of_birth='1980-09-01')
#         HouseholdMember.objects.create(surname='B', household=household_a, date_of_birth='1980-09-01')
#         HouseholdMember.objects.create(surname='C', household=household_a, date_of_birth='1980-09-01')
#         response = self.client.get('/households/')
#
#         self.assertEqual(response.status_code, 200)
#
#         templates = [template.name for template in response.templates]
#
#         self.assertIn('households/index.html', templates)
#         self.assertEqual(len(response.context['households']), 3)
#         self.assertEqual(household_b, response.context['households'][0])
#         self.assertEqual(household_a, response.context['households'][1])
#         self.assertEqual(household_c, response.context['households'][2])
#
#         locations = response.context['location_data'].get_widget_data()
#         self.assertEquals(len(locations['district']), 1)
#         self.assertEquals(locations['district'][0], kampala)
#
#
#     @patch('django.contrib.messages.error')
#     def test_listing_no_households(self, mock_error_message):
#         country = LocationType.objects.create(name="country", slug=slugify("country"))
#         uganda = Location.objects.create(name="Uganda", type=country)
#         district = LocationType.objects.create(name='district', slug='district')
#         village = LocationType.objects.create(name='village', slug='village')
#         LocationTypeDetails.objects.create(country=uganda, location_type=country)
#         LocationTypeDetails.objects.create(country=uganda, location_type=district)
#         LocationTypeDetails.objects.create(country=uganda, location_type=village)
#
#         kampala = Location.objects.create(name="kampala", type=district, tree_parent=uganda)
#
#         investigator = Investigator.objects.create(name="inv", mobile_number='987654321', location=kampala,
#                                                    backend=Backend.objects.create(name='something'))
#         Household.objects.filter(investigator=investigator).delete()
#         response = self.client.get('/households/')
#         self.assertEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('households/index.html', templates)
#
#         self.assertEqual(len(response.context['households']), 0)
#
#         locations = response.context['location_data'].get_widget_data()
#         self.assertEquals(len(locations['district']), 1)
#         self.assertEquals(locations['district'][0], kampala)
#
#     def test_filter_list_investigators_by_location(self):
#         country = LocationType.objects.create(name="Country", slug=slugify("country"))
#         region = LocationType.objects.create(name="Region", slug=slugify("region"))
#         district = LocationType.objects.create(name="District", slug=slugify("district"))
#         county = LocationType.objects.create(name="County", slug=slugify("county"))
#
#         africa = Location.objects.create(name="Africa", type=country)
#         LocationTypeDetails.objects.create(country=africa, location_type=country)
#         LocationTypeDetails.objects.create(country=africa, location_type=region)
#         LocationTypeDetails.objects.create(country=africa, location_type=district)
#         LocationTypeDetails.objects.create(country=africa, location_type=county)
#
#         uganda = Location.objects.create(name="Uganda", type=region, tree_parent=africa)
#         kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
#         bukoto = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala)
#         uganda_ea = EnumerationArea.objects.create(name="EA1")
#         uganda_ea.locations.add(uganda)
#
#         kampla_ea = EnumerationArea.objects.create(name="EA2")
#         kampla_ea.locations.add(kampala)
#
#         bukoto_ea = EnumerationArea.objects.create(name="EA3")
#         bukoto_ea.locations.add(bukoto)
#
#
#         investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", ea=uganda_ea,
#                                                     backend=Backend.objects.create(name='something1'))
#         investigator2 = Investigator.objects.create(name="Investigator", mobile_number="987654322", ea=kampla_ea,
#                                                     backend=Backend.objects.create(name='something2'))
#         investigator3 = Investigator.objects.create(name="Investigator", mobile_number="987654323", ea=bukoto_ea,
#                                                     backend=Backend.objects.create(name='something3'))
#
#         household1 = Household.objects.create(investigator=investigator1, ea=investigator1.ea, uid=0)
#         household2 = Household.objects.create(investigator=investigator2, ea=investigator2.ea, uid=1)
#         household3 = Household.objects.create(investigator=investigator3, ea=investigator3.ea, uid=2)
#
#         response = self.client.get("/households/?location=" + str(uganda.id))
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('households/index.html', templates)
#
#         self.assertEqual(len(response.context['households']), 3)
#         for household in [household1, household2, household3]:
#             self.assertIn(household, response.context['households'])
#
#         response = self.client.get("/households/?location=" + str(kampala.id))
#         self.assertEqual(len(response.context['households']), 2)
#         for household in [household2, household3]:
#             self.assertIn(household, response.context['households'])
#
#         response = self.client.get("/households/?location=" + str(bukoto.id))
#         self.assertEqual(len(response.context['households']), 1)
#         self.assertEqual(household3, response.context['households'][0])
#
#     def test_filter_list_investigators_by_ea(self):
#         country = LocationType.objects.create(name="Country", slug=slugify("country"))
#         region = LocationType.objects.create(name="Region", slug=slugify("region"))
#         district = LocationType.objects.create(name="District", slug=slugify("district"))
#         county = LocationType.objects.create(name="County", slug=slugify("county"))
#
#         africa = Location.objects.create(name="Africa", type=country)
#         LocationTypeDetails.objects.create(country=africa, location_type=country)
#         LocationTypeDetails.objects.create(country=africa, location_type=region)
#         LocationTypeDetails.objects.create(country=africa, location_type=district)
#         LocationTypeDetails.objects.create(country=africa, location_type=county)
#
#         uganda = Location.objects.create(name="Uganda", type=region, tree_parent=africa)
#         kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
#         bukoto = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala)
#         uganda_ea = EnumerationArea.objects.create(name="EA2")
#         uganda_ea.locations.add(uganda)
#
#         kampla_ea = EnumerationArea.objects.create(name="EA2")
#         kampla_ea.locations.add(kampala)
#
#         bukoto_ea = EnumerationArea.objects.create(name="EA2")
#         bukoto_ea.locations.add(bukoto)
#
#
#         investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", ea=uganda_ea,
#                                                     backend=Backend.objects.create(name='something1'))
#         investigator2 = Investigator.objects.create(name="Investigator", mobile_number="987654322", ea=kampla_ea,
#                                                     backend=Backend.objects.create(name='something2'))
#         investigator3 = Investigator.objects.create(name="Investigator", mobile_number="987654323", ea=bukoto_ea,
#                                                     backend=Backend.objects.create(name='something3'))
#
#         household1 = Household.objects.create(investigator=investigator1, ea=investigator1.ea, uid=0)
#         household2 = Household.objects.create(investigator=investigator2, ea=investigator2.ea, uid=1)
#         household3 = Household.objects.create(investigator=investigator3, ea=investigator3.ea, uid=2)
#
#         HouseholdHead.objects.create(surname='Bravo 1', household=household1, date_of_birth='1980-09-01')
#         HouseholdHead.objects.create(surname='Bravo 2', household=household2, date_of_birth='1980-09-01')
#         HouseholdHead.objects.create(surname='Bravo 3', household=household3, date_of_birth='1980-09-01')
#
#
#         response = self.client.get("/households/?ea=" + str(uganda_ea.id))
#         self.failUnlessEqual(response.status_code, 200)
#         templates = [template.name for template in response.templates]
#         self.assertIn('households/index.html', templates)
#
#         self.assertEqual(len(response.context['households']), 1)
#         self.assertEqual(household1, response.context['households'][0])
#
#         response = self.client.get("/households/?ea=" + str(kampla_ea.id))
#         self.assertEqual(len(response.context['households']), 1)
#         self.assertEqual(household2, response.context['households'][0])
#
#         response = self.client.get("/households/?ea=" + str(bukoto_ea.id))
#         self.assertEqual(len(response.context['households']), 1)
#         self.assertEqual(household3, response.context['households'][0])
#
#     def test_restricted_permissions(self):
#         self.assert_restricted_permission_for('/households/')
#
#     def test_sets_location_to_household(self):
#         country = LocationType.objects.create(name="Country", slug=slugify("country"))
#         district = LocationType.objects.create(name="District", slug=slugify("district"))
#         county = LocationType.objects.create(name="County", slug=slugify("county"))
#         sub_county = LocationType.objects.create(name="Subcounty", slug=slugify("sub-county"))
#         parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
#         village = LocationType.objects.create(name="Village", slug=slugify("village"))
#
#         uganda = Location.objects.create(name="Uganda", type=country)
#         kampala_district = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
#         bukoto_county = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala_district)
#         some_sub_county = Location.objects.create(name="Some sub county", type=sub_county, tree_parent=bukoto_county)
#         some_parish = Location.objects.create(name="Some parish", type=parish, tree_parent=some_sub_county)
#         some_village = Location.objects.create(name="Some village", type=village, tree_parent=some_parish)
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(some_village)
#
#         investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321",
#                                                     ea=ea,
#                                                     backend=Backend.objects.create(name='something1'))
#
#         household1 = Household.objects.create(investigator=investigator1, ea=investigator1.ea, uid=0)
#         HouseholdHead.objects.create(surname='Bravo', household=household1, date_of_birth='1980-09-01')
#         household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county',
#                               'Parish': 'Some parish', 'Village': 'Some village'}
#
#         response = self.client.get('/households/')
#         self.assertEqual(response.status_code, 200)
#
#         self.assertEqual(household_location, response.context['households'][0].related_locations)
#
#     def test_should_send_only_number_of_households_sorted_by_head_surname(self):
#         country = LocationType.objects.create(name="country", slug=slugify("country"))
#         uganda = Location.objects.create(name="Uganda", type=country)
#
#         ea = EnumerationArea.objects.create(name="EA2")
#         ea.locations.add(uganda)
#
#         investigator = Investigator.objects.create(name="inv", mobile_number='987654321', ea=ea,
#                                                    backend=Backend.objects.create(name='something'))
#         household_a = Household.objects.create(investigator=investigator, ea=investigator.ea, uid=0)
#         household_b = Household.objects.create(investigator=investigator,  ea=investigator.ea, uid=1)
#         household_c = Household.objects.create(investigator=investigator,  ea=investigator.ea,  uid=2)
#         household_d = Household.objects.create(investigator=investigator,  ea=investigator.ea,  uid=3)
#
#         HouseholdHead.objects.create(surname='Bravo', household=household_b, date_of_birth='1980-09-01')
#         HouseholdHead.objects.create(surname='Alpha', household=household_a, date_of_birth='1980-09-01')
#         HouseholdHead.objects.create(surname='Charlie', household=household_c, date_of_birth='1980-09-01')
#         HouseholdHead.objects.create(surname='Charlie', household=household_d, date_of_birth='1980-09-01')
#
#         HouseholdMember.objects.create(surname='Bravo', first_name='first_member', household=household_b,
#                                        date_of_birth='1980-09-01')
#         HouseholdMember.objects.create(surname='Bravo', first_name='second_member', household=household_b,
#                                        date_of_birth='1980-09-01')
#         HouseholdMember.objects.create(surname='Alpha', first_name='first_member', household=household_a,
#                                        date_of_birth='1980-09-01')
#         HouseholdMember.objects.create(surname='Charlie', first_name='first_member', household=household_c,
#                                        date_of_birth='1980-09-01')
#         HouseholdMember.objects.create(surname='Charlie ', first_name='first_member', household=household_d,
#                                        date_of_birth='1980-09-01')
#         response = self.client.get('/households/')
#
#         self.assertEqual(response.status_code, 200)
#
#         templates = [template.name for template in response.templates]
#
#         self.assertIn('households/index.html', templates)
#         self.assertEqual(len(response.context['households']), 4)
#         self.assertIn(household_b, response.context['households'])
#         self.assertEqual(household_a, response.context['households'][0])
#         self.assertEqual(household_b, response.context['households'][1])
#         self.assertEqual(household_c, response.context['households'][2])
#
#
class ViewHouseholdDetailsTest(BaseTest):
    def test_view_household_details(self):
        client = Client()

        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        city = LocationType.objects.create(name="City", slug=slugify("city"))
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=city, tree_parent=uganda)
        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(kampala)
        survey = Survey.objects.create(name="Test Survey",description="Desc",sample_size=10,has_sampling=True)
        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=investigator,initial_survey=survey)
        household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",
                                             head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=survey)
        HouseholdHead.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                        household=household,survey_listing=survey_householdlisting,
                                        registrar=investigator,registration_channel="ODK Access",
                                        occupation="Agricultural labor",level_of_education="Primary",
                                        resident_since='1989-02-02')

        HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household,survey_listing=survey_householdlisting,
                                                          registrar=investigator,registration_channel="ODK Access")
        response = client.get('/households/%d/' % int(household.id))

        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('households/show.html', templates)
        self.assertEquals(response.context['household'], household)

class EditHouseholdDetailsTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_households')
        self.client.login(username='Rajni', password='I_Rock')
        self.survey = Survey.objects.create(name="Survey A")
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.city = LocationType.objects.create(name="City", parent=self.country, slug="city")
        self.village = LocationType.objects.create(name="Village", parent=self.city, slug="village")
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(name="Kampala", type=self.city, parent=self.uganda)
        self.backend = Backend.objects.create(name='something')
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.country)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.city)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.village)
        self.ea = EnumerationArea.objects.create(name="EA2")
        self.ea.locations.add(self.kampala)
        self.investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=self.ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        self.household_listing = HouseholdListing.objects.create(ea=self.ea,list_registrar=self.investigator,initial_survey=self.survey)
        self.household = Household.objects.create(house_number=123456,listing=self.household_listing,physical_address='Test address',
                                             last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",
                                             head_sex='MALE')
        self.survey_householdlisting = SurveyHouseholdListing.objects.create(listing=self.household_listing,survey=self.survey)
        HouseholdHead.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                        household=self.household,survey_listing=self.survey_householdlisting,
                                        registrar=self.investigator,registration_channel="ODK Access",
                                        occupation="Agricultural labor",level_of_education="Primary",
                                        resident_since='1989-02-02')
#
    def test_get_edit__household_details(self):
        response = self.client.get('/households/%s/edit/' % self.household.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('households/new.html', templates)
        self.assertEquals(response.context['action'], '/households/%s/edit/' % self.household.id)
        self.assertEquals(response.context['id'], 'create-household-form')
        self.assertEquals(response.context['button_label'], 'Save')
        self.assertEquals(response.context['heading'], 'Edit Household')
        self.assertEquals(response.context['loading_text'], 'Creating...')
        investigator_form = {'value': '', 'text': '', 'options': Interviewer.objects.all(), 'error': ''}
        self.assertIsNotNone(response.context['householdform'])
        self.assertIsNotNone(response.context['locations_filter'])

    # def test_post_edit__household_details(self):
    #     new_investigator = Interviewer.objects.create(name="Investigator",
    #                                                ea=self.ea,
    #                                                gender='1',level_of_education='Primary',
    #                                                language='Eglish',weights=0)
    #
    #     form_values = {'investigator': new_investigator.id,
    #                    'location': self.household.location.id,
    #                    'uid': self.household.uid, 'ea': new_investigator.ea.id}
    #     response = self.client.post('/households/%s/edit/' % self.household.id, data=form_values)
    #
    #     self.assertRedirects(response, '/households/', 302, 200)
    #     updated_household = Household.objects.get(id=self.household.id)
    #     self.assertNotEqual(updated_household.investigator, self.investigator)
    #     self.assertEqual(updated_household.investigator, new_investigator)
    #     updated_investigator = Interviewer.objects.get(id=self.investigator.id)
    #     self.assertEqual(0, len(updated_investigator.households.all()))
    #     self.assertEqual(1, len(new_investigator.households.all()))
    #     success_message = "Household successfully edited."
    #     self.assertIn(success_message, response.cookies['messages'].value)
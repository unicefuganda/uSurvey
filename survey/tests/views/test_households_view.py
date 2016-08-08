import json
from django.template.defaultfilters import slugify
from datetime import date
from django.test.client import Client
from mock import *
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
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
        self.assertIsNotNone(response.context['householdform'])
        self.assertIsNotNone(response.context['headform'])
        self.assertIsNotNone(response.context['locations_filter'])

    def testlist_households(self):
        response = self.client.get('/households/')
        self.failUnlessEqual(response.status_code, 200)

    def testlist_households(self):
        response = self.client.get('/households/download/')
        self.failUnlessEqual(response.status_code, 200)

    def test_get_investigators_failures(self):
        response = self.client.get('/households/interviewers')
        self.failUnlessEqual(response.status_code, 200)
        result_investigator = json.loads(response.content)
        self.failUnlessEqual(result_investigator, {})

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

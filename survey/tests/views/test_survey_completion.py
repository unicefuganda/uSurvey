import datetime
import json
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.test import Client
from survey.models.locations import *
# from survey.models import Survey, Batch, Indicator, Household, Question, HouseholdMemberGroup, \
#     HouseholdMemberBatchCompletion, Backend, LocationTypeDetails, EnumerationArea, Interviewer, HouseholdListing, \
#     SurveyHouseholdListing, SurveyAllocation
# from survey.models.households import HouseholdMember
from survey.models import Survey, Batch, Indicator, Question, Backend, EnumerationArea, Interviewer, SurveyAllocation
# from survey.services.completion_rates_calculator import BatchLocationCompletionRates
from survey.tests.base_test import BaseTest
from survey.views.survey_completion import is_valid


class TestSurveyCompletion(BaseTest):

    def setUp(self):
        self.client = Client()
        User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_aggregates')
        self.client.login(username='Rajni', password='I_Rock')
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.region = LocationType.objects.create(
            name='Region', parent=self.country, slug='region')
        self.city = LocationType.objects.create(
            name='City', parent=self.region, slug='city')
        self.parish = LocationType.objects.create(
            name='Parish', parent=self.city, slug='parish')
        self.survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)

        self.africa = Location.objects.create(name='Africa', type=self.country)
        LocationTypeDetails.objects.create(
            country=self.africa, location_type=self.country)
        LocationTypeDetails.objects.create(
            country=self.africa, location_type=self.region)
        LocationTypeDetails.objects.create(
            country=self.africa, location_type=self.city)
        LocationTypeDetails.objects.create(
            country=self.africa, location_type=self.parish)

        self.uganda = Location.objects.create(
            name='Uganda', type=self.region, parent=self.africa)
        self.abim = Location.objects.create(
            name='Abim', parent=self.uganda, type=self.city)
        self.kampala = Location.objects.create(
            name='Kampala', parent=self.uganda, type=self.city)
        self.bukoto = Location.objects.create(
            name='Kampala City', parent=self.kampala, type=self.parish)
        self.kampala_ea = EnumerationArea.objects.create(name="EA2")
        self.kampala_ea.locations.add(self.kampala)
        self.abim_ea = EnumerationArea.objects.create(name="ABIM EA")
        self.abim_ea.locations.add(self.abim)

        self.city_ea = EnumerationArea.objects.create(name="CITY EA")
        self.city_ea.locations.add(self.bukoto)

        self.investigator_1 = Interviewer.objects.create(name="Investigator",
                                                         ea=self.kampala_ea,
                                                         gender='1', level_of_education='Primary',
                                                         language='Eglish', weights=0)
        self.investigator_2 = Interviewer.objects.create(name="Investigator",
                                                         ea=self.city_ea,
                                                         gender='1', level_of_education='Primary',
                                                         language='Eglish', weights=0)

        self.household_listing = HouseholdListing.objects.create(
            ea=self.kampala_ea, list_registrar=self.investigator_1, initial_survey=self.survey)
        self.household = Household.objects.create(house_number=123456, listing=self.household_listing, physical_address='Test address',
                                                  last_registrar=self.investigator_1, registration_channel="ODK Access", head_desc="Head",
                                                  head_sex='MALE')
        self.household_listing_1 = HouseholdListing.objects.create(
            ea=self.city_ea, list_registrar=self.investigator_2, initial_survey=self.survey)
        self.household_1 = Household.objects.create(house_number=1234567, listing=self.household_listing_1, physical_address='Test address',
                                                    last_registrar=self.investigator_2, registration_channel="ODK Access", head_desc="Head",
                                                    head_sex='MALE')
        self.survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=self.household_listing, survey=self.survey)
        self.member_1 = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                       household=self.household, survey_listing=self.survey_householdlisting,
                                                       registrar=self.investigator_1, registration_channel="ODK Access")
        self.survey_householdlisting_1 = SurveyHouseholdListing.objects.create(
            listing=self.household_listing_1, survey=self.survey)
        self.member_2 = HouseholdMember.objects.create(surname="sur1", first_name='fir1', gender='MALE', date_of_birth="1988-01-01",
                                                       household=self.household_1, survey_listing=self.survey_householdlisting_1,
                                                       registrar=self.investigator_2, registration_channel="ODK Access")

        self.batch = Batch.objects.create(
            order=1, name='somebatch', survey=self.survey)

    def test_should_render_success_status_code_on_GET(self):
        response = self.client.get('/surveys/completion/')
        self.assertEqual(response.status_code, 200)

    def test_should_render_template(self):
        response = self.client.get('/surveys/completion/')
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/completion_status.html', templates)

    def test_survey_completion_summary(self):
        SurveyAllocation.objects.create(
            interviewer=self.investigator_1, survey=self.survey, allocation_ea=self.kampala_ea, stage=1, status=0)
        response = self.client.get(
            '/surveys/completion_summary/%d/%d' % (self.household.id, self.batch.id))
        self.assertEqual(response.status_code, 200)

    def test_location_completion_summary(self):
        response = self.client.get(
            '/surveys/locations_completion_summary/%d/%d' % (self.kampala.id, self.batch.id))
        self.assertEqual(response.status_code, 200)

    def test_validates_when_location_is_present_in_parameters_and_parameters_contains_batch_key(self):
        self.assertTrue(is_valid({'location': '', 'batch': '1'}))
        self.assertTrue(is_valid({'location': '2', 'batch': '1', 'ea': '1'}))
        self.assertTrue(is_valid({'location': '2', 'batch': '1', 'ea': ''}))

    def test_show_retrieves_high_level_completion_rates_if_no_location_is_provided(self):
        data = {'location': '',
                'batch': str(self.batch.pk),
                'survey': self.survey.id,
                'ea': ''}
        response = self.client.post('/surveys/completion/', data=data)
        self.assertIsNotNone(response.context['request'])

    def test_knows_to_retrieve_completion_for_locations_that_have_no_tree_parent_if_country_type_does_not_exist(self):
        LocationType.objects.filter(name__iexact='country').delete()
        location_with_no_parent = Location.objects.create(
            name='Unganda1', type=self.country)
        another_location_with_no_parent = Location.objects.create(
            name='Unganda12', type=self.country)
        form_data = {'survey': self.batch.survey.id, 'location': location_with_no_parent.id, 'batch': str(
            self.batch.pk), 'ea': self.kampala_ea.id}
        response = self.client.post('/surveys/completion/', data=form_data)
        self.assertIsNotNone(response.context['request'])

    def test_survey_completion(self):
        response = self.client.get(
            '/survey/%d/completion/json/' % (self.survey.id))
        result = json.loads(response.getvalue())
        self.assertEqual(response.status_code, 200)
        location = self.uganda.name.upper()
        self.assertEqual(int(result[location]), 0)


from survey.models.locations import *

from survey.models import Batch
from survey.models import EnumerationArea
from survey.models import Survey
# from survey.models.batch_question_order import BatchQuestionOrder
from survey.models.householdgroups import HouseholdMemberGroup
from survey.models.households import Household
from survey.models.households import HouseholdListing
from survey.models.households import HouseholdMember
from survey.models.households import SurveyHouseholdListing
from survey.models.interviewer import Interviewer
from survey.tests.base_test import BaseTest


class HouseholdMemberTest(BaseTest):

    def setUp(self):
        self.batch = Batch.objects.create(name="BATCH 1", order=1)

    def test_should_have_fields_required(self):
        household_member = HouseholdMember()
        fields = [str(item.attname) for item in household_member._meta.fields]

        field_list_expected = ['id', 'created', 'modified', 'surname', 'first_name', 'gender',
                               'date_of_birth', 'household_id', 'survey_listing_id', 'registrar_id', 'registration_channel']

        [self.assertIn(field_expected, fields)
         for field_expected in field_list_expected]

    def test_should_validate_household_member_belongs_to_household(self):
        country = LocationType.objects.create(name="Country", slug='country')
        district = LocationType.objects.create(
            name="District", parent=country, slug='district')
        county = LocationType.objects.create(
            name="County", parent=district, slug='county')
        subcounty = LocationType.objects.create(
            name="SubCounty", parent=county, slug='subcounty')
        parish = LocationType.objects.create(
            name="Parish", parent=subcounty, slug='parish')
        village = LocationType.objects.create(
            name="Village", parent=parish, slug='village')

        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, parent=uganda)
        some_county = Location.objects.create(
            name="County", type=county, parent=kampala)
        some_sub_county = Location.objects.create(
            name="Subcounty", type=subcounty, parent=some_county)
        some_parish = Location.objects.create(
            name="Parish", type=parish, parent=some_sub_county)
        some_village = Location.objects.create(
            name="Village", type=village, parent=some_parish)
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        # ea.locations.add(kampala)
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)

        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')
#        fields_data = dict(surname='xyz', male=True, date_of_birth=date(1980, 05, 01), household=household)
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household, survey_listing=survey_householdlisting,
                                                          registrar=investigator, registration_channel="ODK Access")
        self.failUnless(household_member)
        self.assertEqual(household_member.surname, 'sur')
        self.assertTrue(household_member.gender)
        self.assertEqual(household_member.date_of_birth, '1988-01-01')
        self.assertEqual(household_member.household, household)

    def test_household_members_count_per_location_in(self):
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        batch = Batch.objects.create(name="BATCH 1", order=1, survey=survey)
        country = LocationType.objects.create(name="Country1", slug='country')
        district = LocationType.objects.create(
            name="District1", parent=country, slug='district')
        county = LocationType.objects.create(
            name="County1", parent=district, slug='county')
        subcounty = LocationType.objects.create(
            name="SubCounty1", parent=county, slug='subcounty')
        parish = LocationType.objects.create(
            name="Parish1", parent=subcounty, slug='parish')
        village = LocationType.objects.create(
            name="Village1", parent=parish, slug='village')

        uganda = Location.objects.create(name="Uganda1", type=country)
        kampala = Location.objects.create(
            name="Kampala1", type=district, parent=uganda)
        some_county = Location.objects.create(
            name="County1", type=county, parent=kampala)
        ea1 = EnumerationArea.objects.create(name="EA Area")
        batch.open_for_location(kampala)
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea1,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        household_listing = HouseholdListing.objects.create(
            ea=ea1, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household, survey_listing=survey_householdlisting,
                                                          registrar=investigator, registration_channel="ODK Access")
        household_member_group = HouseholdMemberGroup.objects.create(
            name="test name", order=1)
        locations = [kampala, ]
        self.assertEqual(kampala, household_member_group.household_members_count_per_location_in(
            locations, survey).keys()[0])

    def test_hierarchical_result_for(self):
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        batch = Batch.objects.create(name="BATCH 11", order=1, survey=survey)
        country = LocationType.objects.create(name="Country11", slug='country')
        district = LocationType.objects.create(
            name="District11", parent=country, slug='district')
        county = LocationType.objects.create(
            name="County11", parent=district, slug='county')
        subcounty = LocationType.objects.create(
            name="SubCounty11", parent=county, slug='subcounty')
        parish = LocationType.objects.create(
            name="Parish11", parent=subcounty, slug='parish')
        village = LocationType.objects.create(
            name="Village11", parent=parish, slug='village')

        uganda = Location.objects.create(name="Uganda11", type=country)
        kampala = Location.objects.create(
            name="Kampala11", type=district, parent=uganda)
        some_county = Location.objects.create(
            name="County11", type=county, parent=kampala)
        ea1 = EnumerationArea.objects.create(name="EA Area1")
        batch.open_for_location(kampala)
        investigator = Interviewer.objects.create(name="Investigator111",
                                                  ea=ea1,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        household_listing = HouseholdListing.objects.create(
            ea=ea1, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=12345611, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur11", first_name='fir11', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household, survey_listing=survey_householdlisting,
                                                          registrar=investigator, registration_channel="ODK Access")
        household_member_group = HouseholdMemberGroup.objects.create(
            name="test name11", order=1)
        self.assertEqual(some_county, household_member_group.hierarchical_result_for(
            kampala, survey).keys()[0])

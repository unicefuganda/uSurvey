from django.test import TestCase
from survey.models.locations import *
from survey.models import HouseholdMemberGroup, GroupCondition, Question, Batch, HouseholdMemberBatchCompletion, \
    NumericalAnswer, Survey, EnumerationArea, QuestionModule
# from survey.models.batch_question_order import BatchQuestionOrder
from survey.models.households import Household, HouseholdListing, HouseholdMember, SurveyHouseholdListing
from survey.models.interviewer import Interviewer


class HouseholdTest(TestCase):

    def setUp(self):
        self.country = LocationType.objects.create(
            name="Country", slug='country')
        self.district = LocationType.objects.create(
            name="District", parent=self.country, slug='district')
        self.county = LocationType.objects.create(
            name="County", parent=self.district, slug='county')
        self.subcounty = LocationType.objects.create(
            name="SubCounty", parent=self.county, slug='subcounty')
        self.parish = LocationType.objects.create(
            name="Parish", parent=self.subcounty, slug='parish')
        self.village = LocationType.objects.create(
            name="Village", parent=self.parish, slug='village')

        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(
            name="Kampala", type=self.district, parent=self.uganda)
        self.some_county = Location.objects.create(
            name="County", type=self.county, parent=self.kampala)
        self.some_sub_county = Location.objects.create(
            name="Subcounty", type=self.subcounty, parent=self.some_county)
        self.some_parish = Location.objects.create(
            name="Parish", type=self.parish, parent=self.some_sub_county)
        self.some_village = Location.objects.create(
            name="Village", type=self.village, parent=self.some_parish)
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(self.kampala)

        self.investigator = Interviewer.objects.create(name="Investigator",
                                                       ea=ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0)

        self.survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        self.household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=self.investigator, initial_survey=self.survey)
        self.household = Household.objects.create(house_number=123456, listing=self.household_listing, physical_address='Test address',
                                                  last_registrar=self.investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')
        self.survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=self.household_listing, survey=self.survey)
        self.household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                               household=self.household, survey_listing=self.survey_householdlisting,
                                                               registrar=self.investigator, registration_channel="ODK Access")

    def test_fields(self):
        hHead = Household()
        fields = [str(item.attname) for item in hHead._meta.fields]

        self.assertEqual(len(fields), 10)
        for field in ['id', 'created', 'modified', 'house_number', 'listing_id',
                      'physical_address', 'last_registrar_id', 'registration_channel', 'head_desc', 'head_sex']:
            self.assertIn(field, fields)

    def test_store(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A1243")
        investigator = Interviewer.objects.create(name="Investigator123",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        survey = Survey.objects.create(
            name="Test Survey3214", description="Desc234", sample_size=10, has_sampling=True)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=self.investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access",
                                             head_desc="Head", head_sex='MALE')
        self.failUnless(household.id)
        self.failUnless(household.created)
        self.failUnless(household.modified)

from django.test import TestCase
from survey.models.locations import LocationType, Location
from survey.models import EnumerationArea
from survey.models import Interviewer
from survey.models.households import Household
from survey.models.households import HouseholdHead
from survey.models.households import HouseholdListing
from survey.models.households import SurveyHouseholdListing
from survey.models.surveys import Survey


class HouseholdHeadTest(TestCase):

    def test_fields(self):
        hHead = HouseholdHead()
        fields = [str(item.attname) for item in hHead._meta.fields]
        self.assertEqual(len(fields), 15)
        for field in ['id', 'created', 'modified', 'surname', 'first_name', 'gender', 'date_of_birth', 'household_id', 'survey_listing_id',
                      'registrar_id', 'registration_channel', 'householdmember_ptr_id', 'occupation', 'level_of_education', 'resident_since']:
            self.assertIn(field, fields)

    def test_store(self):
        self.location_type_country = LocationType.objects.create(
            name="Country", slug='country')
        self.location_type_district = LocationType.objects.create(
            name="District", parent=self.location_type_country, slug='district')
        self.location_type_county = LocationType.objects.create(
            name="County", parent=self.location_type_district, slug='county')
        self.location_type_subcounty = LocationType.objects.create(
            name="SubCounty", parent=self.location_type_county, slug='subcounty')
        self.location_type_parish = LocationType.objects.create(
            name="Parish", parent=self.location_type_subcounty, slug='parish')
        self.location_type_village = LocationType.objects.create(
            name="Village", parent=self.location_type_parish, slug='village')

        self.country = Location.objects.create(name="Country", type=self.location_type_country, code=256
                                               )
        self.district = Location.objects.create(name="District", type=self.location_type_country, parent=self.country, code=256
                                                )
        self.county = Location.objects.create(name="County", type=self.location_type_county, parent=self.district, code=256
                                              )
        ea = EnumerationArea.objects.create(name="Kampala EA A")
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

        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        hHead = HouseholdHead.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                             household=household, survey_listing=survey_householdlisting,
                                             registrar=investigator, registration_channel="ODK Access", occupation="Agricultural labor", level_of_education="Primary",
                                             resident_since='1989-02-02')
        self.failUnless(hHead.id)
        self.failUnless(hHead.created)
        self.failUnless(hHead.modified)

    def test_knows_household_member_from_head(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A")
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

        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        hHead = HouseholdHead.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                             household=household, survey_listing=survey_householdlisting,
                                             registrar=investigator, registration_channel="ODK Access", occupation="Agricultural labor", level_of_education="Primary",
                                             resident_since='1989-02-02')

        self.assertIs(hHead.is_head(), True)

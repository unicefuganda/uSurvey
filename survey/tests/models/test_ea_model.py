from survey.models.locations import Location, LocationType
from survey.models import Survey, LocationTypeDetails, Interviewer, Household, HouseholdListing, SurveyHouseholdListing, HouseholdMember
from survey.models.householdgroups import HouseholdMemberGroup
from survey.models.batch import Batch
from survey.models.enumeration_area import EnumerationArea
from survey.tests.base_test import BaseTest


class EATest(BaseTest):
    def setUp(self):
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1, survey=self.survey)
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.region = LocationType.objects.create(name="Region", slug="region", parent=self.country)
        self.district = LocationType.objects.create(name="District", slug='district', parent=self.region)

        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        LocationTypeDetails.objects.create(location_type=self.country, country=self.uganda)
        self.west = Location.objects.create(name="WEST", type=self.region, parent=self.uganda)
        self.central = Location.objects.create(name="CENTRAL", type=self.region, parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", parent=self.central, type=self.district)
        self.wakiso = Location.objects.create(name="Wakiso", parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", parent=self.west, type=self.district)

    def test_ea_fields(self):
        ea = EnumerationArea()

        fields = [str(item.attname) for item in ea._meta.fields]
        for field in ['id', 'name', 'created', 'modified', 'code']:
            self.assertIn(field, fields)
        self.assertEqual(len(fields), 5)

    def test_store(self):
        ea = EnumerationArea.objects.create(name="EA1")
        self.failUnless(ea.id)

    def test_add_location(self):
        self.location_type_country = LocationType.objects.create(name="Country1", slug='country1')
        self.location_type_district = LocationType.objects.create(name="District2", parent=self.location_type_country,slug='district2')
        self.location_type_district1 = LocationType.objects.create(name="District1", parent=self.location_type_country,slug='district1')
        self.location = Location.objects.create(name="Kangala", type=self.location_type_country, code=256)
        self.locations_district=Location.objects.create(name="dist",type=self.district,code=234)
        self.locations_district1=Location.objects.create(name="dist1",type=self.district,code=234)
        ea = EnumerationArea.objects.create(name="EA1")

    def test_get_survey_openings(self):
        ea_new=EnumerationArea.objects.create(name="new EA")
        ea_new.locations.add(self.kampala)
        self.batch.open_for_location(self.kampala)
        self.assertTrue(self.survey.is_open_for(self.kampala))
        self.assertEquals(self.batch.pk, ea_new.get_survey_openings(self.survey).values()[0]["batch_id"])

    def test_open_batches(self):
        ea1=EnumerationArea.objects.create(name="new EA")
        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea1,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        ea1.locations.add(self.kampala)
        household_listing = HouseholdListing.objects.create(ea=ea1,list_registrar=investigator,initial_survey=self.survey)
        household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=self.survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household,survey_listing=survey_householdlisting,
                                                          registrar=investigator,registration_channel="ODK Access")
        household_member_group = HouseholdMemberGroup.objects.create(name="test name", order=1)
        self.assertEqual([],ea1.open_batches(self.survey,house_member=household_member))
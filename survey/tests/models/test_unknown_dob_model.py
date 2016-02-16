from datetime import date
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models.locations import Location, LocationType
from survey.models import Interviewer, Household, Backend, EnumerationArea
from survey.models.households import HouseholdMember, HouseholdListing, SurveyHouseholdListing
from survey.models.unknown_dob_attribute import UnknownDOBAttribute
from survey.tests.base_test import BaseTest
from survey.models.surveys import Survey


class UnknownDOBAttributeTest(BaseTest):
    def test_fields(self):
        unknown_dob = UnknownDOBAttribute()
        fields = [str(item.attname) for item in unknown_dob._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'household_member_id', 'type']:
            self.assertIn(field, fields)

    def test_store(self):
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(name="City", slug="city")
        subcounty = LocationType.objects.create(name="Subcounty", slug="subcounty")
        parish = LocationType.objects.create(name="Parish", slug="parish")
        village = LocationType.objects.create(name="Village", slug="village")
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=city, tree_parent=uganda)
        abim = Location.objects.create(name="Abim", type=subcounty, tree_parent=kampala)
        kololo = Location.objects.create(name="Kololo", type=parish, tree_parent=abim)
        village = Location.objects.create(name="Village", type=village, tree_parent=kololo)
        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(kampala)
        survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)

        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=investigator,initial_survey=survey)
        household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",
                                             head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household,survey_listing=survey_householdlisting,
                                                          registrar=investigator,registration_channel="ODK Access")

        unknown_dob = UnknownDOBAttribute.objects.create(household_member=household_member, type="MONTH" )

        self.failUnless(unknown_dob.id)

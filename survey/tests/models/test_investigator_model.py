
from django.test import TestCase
from survey.models import EnumerationArea
from survey.models.locations import *
from survey.models.backend import Backend
from survey.models.households import Household, HouseholdMember
from survey.models.interviewer import Interviewer
from survey.models import HouseholdListing
from survey.models import SurveyHouseholdListing
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition
from survey.models.surveys import Survey


class InvestigatorTest(TestCase):

    def setUp(self):
        self.member_group = HouseholdMemberGroup.objects.create(
            name="Greater than 2 years", order=1)
        self.condition = GroupCondition.objects.create(
            attribute="AGE", value=2, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.district = LocationType.objects.create(
            name='District', parent=self.country, slug='district')
        self.survey = Survey.objects.create(name="haha")
        self.backend = Backend.objects.create(name='something')
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(
            name="Kampala", type=self.district, parent=self.uganda)
        self.ea = EnumerationArea.objects.create(name="EA1")
        self.ea.locations.add(self.kampala)

        self.investigator = Interviewer.objects.create(name="Investigator",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0)

        self.household_listing = HouseholdListing.objects.create(
            ea=self.ea, list_registrar=self.investigator, initial_survey=self.survey)
        self.household = Household.objects.create(house_number=123456, listing=self.household_listing, physical_address='Test address',
                                                  last_registrar=self.investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')
        self.survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=self.household_listing, survey=self.survey)
        self.household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                               household=self.household, survey_listing=self.survey_householdlisting,
                                                               registrar=self.investigator, registration_channel="ODK Access")

    def test_generate_survey_households(self):
        investigator1 = Interviewer.objects.create(name="Investigator1",
                                                   ea=self.ea,
                                                   gender='1', level_of_education='Primary',
                                                   language='Eglish', weights=0)

        self.assertEqual(
            self.household, investigator1.generate_survey_households(self.survey)[0])

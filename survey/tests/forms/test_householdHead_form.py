from datetime import datetime, date

from django.test import TestCase

from survey.forms.householdHead import *
from survey.models.households import HouseholdHead, Household
from survey.models.interviewer import Interviewer
from survey.models import Survey, HouseholdListing, EnumerationArea, SurveyHouseholdListing


class MockDate(datetime):

    @classmethod
    def now(cls):
        return cls(datetime.now().year, 1, 1)


class HouseholdHeadFormTest(TestCase):

    def setUp(self):
        self.form_data = {
            'surname': 'household',
            'first_name': 'bla',
            'gender': 0,
            'date_of_birth': date(1980, 05, 01),
            'level_of_education': 'Primary',
            'occupation': 'Brewing',
            'resident_since': date(2013, 05, 01)
        }

    def test_valid(self):
        hHead_form = HouseholdHeadForm(self.form_data)
        self.assertTrue(hHead_form.is_valid())
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head",
                                             head_sex='MALE')
        hHead_form.instance.household = household
        hHead_form.instance.survey_listing = survey_householdlisting
        hHead_form.instance.registrar_id = investigator.id
        hHead = hHead_form.save()
        self.failUnless(hHead.id)
        hHead_retrieved = HouseholdHead.objects.get(household=household)
        self.assertEqual(hHead_retrieved, hHead)

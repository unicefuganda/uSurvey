from datetime import date, datetime
from django.template.defaultfilters import slugify
from mock import patch
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models.locations import *
from survey.models import Batch, Interviewer, Household, Question, Backend, Survey, HouseholdMemberBatchCompletion, EnumerationArea, \
    HouseholdListing, SurveyHouseholdListing, QuestionModule, HouseholdMemberGroup
from survey.models.households import HouseholdMember
from survey.services.completion_rates_calculator import BatchCompletionRates, BatchLocationCompletionRates, BatchHighLevelLocationsCompletionRates, BatchSurveyCompletionRates
from survey.tests.base_test import BaseTest


class BatchCompletionRatesTest(BaseTest):
    def setUp(self):
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.city = LocationType.objects.create(name='City', slug='city', parent=self.country)
        self.open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)

        self.uganda = Location.objects.create(name='Uganda', type=self.country)
        self.abim = Location.objects.create(name='Abim', parent=self.uganda, type=self.city)
        self.kampala = Location.objects.create(name='Kampala', parent=self.uganda, type=self.city)
        self.kampala_city = Location.objects.create(name='Kampala City', parent=self.kampala, type=self.city)
        self.ea = EnumerationArea.objects.create(name="EA2")
        self.ea.locations.add(self.kampala)

        self.ea_kla_city = EnumerationArea.objects.create(name="EA2")
        self.ea_kla_city.locations.add(self.kampala_city)

        self.investigator_1 = Interviewer.objects.create(name="Investigator",
                                                   ea=self.ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        self.investigator_2 = Interviewer.objects.create(name="Investigator1",
                                                   ea=self.ea_kla_city,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        self.batch = Batch.objects.create(order=1, name='somebatch', survey=self.open_survey)
        self.household_listing = HouseholdListing.objects.create(ea=self.ea,list_registrar=self.investigator_1,initial_survey=self.open_survey)
        self.household_1 = Household.objects.create(house_number=123456,listing=self.household_listing,physical_address='Test address',
                                             last_registrar=self.investigator_1,registration_channel="ODK Access",head_desc="Head",
                                                       head_sex='MALE')
        self.household_2 = Household.objects.create(house_number=1234567,listing=self.household_listing,physical_address='Test address',
                                             last_registrar=self.investigator_1,registration_channel="ODK Access",head_desc="Head",
                                                       head_sex='MALE')
        self.survey_householdlisting = SurveyHouseholdListing.objects.create(listing=self.household_listing,survey=self.open_survey)
        self.member_1 = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=self.household_1,survey_listing=self.survey_householdlisting,
                                                          registrar=self.investigator_1,registration_channel="ODK Access")
        self.member_2 = HouseholdMember.objects.create(surname="sur1", first_name='fir1', gender='MALE', date_of_birth="1988-01-01",
                                                          household=self.household_1,survey_listing=self.survey_householdlisting,
                                                          registrar=self.investigator_1,registration_channel="ODK Access")
        self.question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        self.household_member_group = HouseholdMemberGroup.objects.create(name="test name1324", order=12)
        self.question = Question.objects.create(identifier='123.1',text="This is a question", answer_type='Numerical Answer',
                                           group=self.household_member_group,batch=self.batch,module=self.question_mod)

    def test_calculate_percent(self):
        completion_rate = BatchCompletionRates(self.batch)
        self.assertEqual(40, completion_rate.calculate_percent(4, 10))
        self.assertEqual(80, completion_rate.calculate_percent(80, 100))
        self.assertEqual(20, completion_rate.calculate_percent(1, 5))
        self.assertEqual(12, completion_rate.calculate_percent(60, 500))
        self.assertEqual(0, completion_rate.calculate_percent(0, 0))
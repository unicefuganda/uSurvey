from datetime import date, datetime
from django.template.defaultfilters import slugify
from mock import patch
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import Batch, Investigator, Household, Question, Backend, Survey, HouseholdMemberBatchCompletion, EnumerationArea
from survey.models.households import HouseholdMember
from survey.services.completion_rates_calculator import BatchCompletionRates, BatchLocationCompletionRates, BatchHighLevelLocationsCompletionRates, BatchSurveyCompletionRates
from survey.tests.base_test import BaseTest


class BatchCompletionRatesTest(BaseTest):
    def setUp(self):
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.city = LocationType.objects.create(name='City', slug='city')
        self.open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)

        self.uganda = Location.objects.create(name='Uganda', type=self.country)
        self.abim = Location.objects.create(name='Abim', tree_parent=self.uganda, type=self.city)
        self.kampala = Location.objects.create(name='Kampala', tree_parent=self.uganda, type=self.city)
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)
        self.ea = EnumerationArea.objects.create(name="EA2", survey=self.open_survey)
        self.ea.locations.add(self.kampala)

        self.ea_kla_city = EnumerationArea.objects.create(name="EA2", survey=self.open_survey)
        self.ea_kla_city.locations.add(self.kampala_city)

        self.investigator_1 = Investigator.objects.create(name='some_inv', mobile_number='123456789', male=True,
                                                          ea=self.ea)
        self.investigator_2 = Investigator.objects.create(name='some_inv', mobile_number='123456788', male=True,
                                                          ea=self.ea_kla_city)

        self.household_1 = Household.objects.create(investigator=self.investigator_1, location=self.kampala_city,
                                                    survey=self.open_survey)
        self.household_2 = Household.objects.create(investigator=self.investigator_1, location=self.kampala_city,
                                                    survey=self.open_survey)

        self.batch = Batch.objects.create(order=1, name='somebatch', survey=self.open_survey)
        self.member_1 = HouseholdMember.objects.create(household=self.household_1, date_of_birth=date(1980, 05, 01))
        self.member_2 = HouseholdMember.objects.create(household=self.household_2, date_of_birth=date(1980, 05, 3))

        self.question = Question.objects.create(text="This is a question",
                                                answer_type=Question.MULTICHOICE)
        self.question.batches.add(self.batch)


    def test_calculate_percent(self):
        completion_rate = BatchCompletionRates(self.batch)
        self.assertEqual(40, completion_rate.calculate_percent(4, 10))
        self.assertEqual(80, completion_rate.calculate_percent(80, 100))
        self.assertEqual(20, completion_rate.calculate_percent(1, 5))
        self.assertEqual(12, completion_rate.calculate_percent(60, 500))
        self.assertEqual(0, completion_rate.calculate_percent(4, 0))

    def test_percentage_completed(self):
        completion_rate = BatchCompletionRates(self.batch)
        self.batch.completed_households.create(householdmember=self.member_1)
        self.assertEqual(50, completion_rate.percentage_completed(
            Household.all_households_in(self.investigator_1.location, self.open_survey)))
        self.batch.completed_households.create(householdmember=self.member_2)
        self.assertEqual(100, completion_rate.percentage_completed(
            Household.all_households_in(self.investigator_1.location, self.open_survey)))

    def test_percent_completed_households(self):
        completion_rate = BatchCompletionRates(self.batch)
        self.batch.completed_households.create(householdmember=self.member_1)
        self.assertEqual(50, completion_rate.percent_completed_households(self.investigator_1.location,
                                                                          self.open_survey))
        self.batch.completed_households.create(householdmember=self.member_2)
        self.assertEqual(100, completion_rate.percent_completed_households(self.investigator_1.location,
                                                                           self.open_survey))

    def test_interviewed_households(self):
        completion_rate = BatchLocationCompletionRates(self.batch, self.investigator_1.location)
        batch_member_completion, b = self.member_1.batch_completed(self.batch)
        date_1 = datetime(1999, 2, 4, 23, 1, 2).replace(tzinfo=batch_member_completion.created.tzinfo)
        batch_member_completion.created = date_1
        batch_member_completion.save()
        interviewed_households = completion_rate.interviewed_households()
        self.assertEqual(2, len(interviewed_households))
        index_of_household_1 = [index for index, interviewed in enumerate(interviewed_households) if
                                interviewed_households[index]['household'] == self.household_1]
        interviewed_1 = interviewed_households[index_of_household_1[0]]
        self.assertEqual(date_1.strftime('%d-%b-%Y %H:%M:%S'), interviewed_1['date_interviewed'])
        self.assertEqual(1, interviewed_1['number_of_member_interviewed'])
        interviewed_households.remove(interviewed_1)
        interviewed_2 = interviewed_households[0]
        self.assertEqual(None, interviewed_2['date_interviewed'])
        self.assertEqual(0, interviewed_2['number_of_member_interviewed'])

        batch_member_completion, b = self.member_2.batch_completed(self.batch)

        date_2 = datetime(1997, 2, 4, 23, 1, 2).replace(tzinfo=batch_member_completion.created.tzinfo)
        batch_member_completion.created = date_2
        batch_member_completion.save()
        interviewed_households = completion_rate.interviewed_households()
        self.assertEqual(2, len(interviewed_households))
        index_of_household_1 = [index for index, interviewed in enumerate(interviewed_households) if
                                interviewed_households[index]['household'] == self.household_1]
        interviewed_1 = interviewed_households[index_of_household_1[0]]
        self.assertEqual(date_1.strftime('%d-%b-%Y %H:%M:%S'), interviewed_1['date_interviewed'])
        self.assertEqual(1, interviewed_1['number_of_member_interviewed'])
        interviewed_households.remove(interviewed_1)
        interviewed_2 = interviewed_households[0]
        self.assertEqual(date_2.strftime('%d-%b-%Y %H:%M:%S'), interviewed_2['date_interviewed'])
        self.assertEqual(1, interviewed_2['number_of_member_interviewed'])

    @patch('survey.services.completion_rates_calculator.BatchCompletionRates.percent_completed_households')
    def test_completion_rates(self, mock_percent):
        masaka = Location.objects.create(name="masaka", tree_parent=self.uganda, type=self.city)
        investigator_3 = Investigator.objects.create(name='some_inv_2', mobile_number='123456787', male=True,
                                                     location=masaka)

        household_3 = Household.objects.create(investigator=investigator_3, location=masaka,
                                               survey=self.open_survey)
        member_3 = HouseholdMember.objects.create(household=household_3, date_of_birth=date(1980, 05, 01))
        mock_percent.side_effect = [self.kampala_city.id, self.open_survey] # return value only needed to change with locations

        completion_rate = BatchHighLevelLocationsCompletionRates(self.batch, [self.kampala_city])
        completions = completion_rate.attributes()
        self.assertEqual(1, len(completions))

        completion_1 = completions[0]
        self.assertEqual(2, completion_1['total_households'])
        self.assertEqual(self.kampala_city.id, completion_1['completed_households_percent'])

        completions.remove(completion_1)
        mock_percent.side_effect = [masaka.id, self.open_survey] # return value only needed to change with locations
        completion_rate = BatchHighLevelLocationsCompletionRates(self.batch, [masaka])

        completions = completion_rate.attributes()
        self.assertEqual(1, len(completions))

        completion_2 = completions[0]
        self.assertEqual(1, completion_2['total_households'])
        self.assertEqual(masaka.id, completion_2['completed_households_percent'])


class BatchSurveyCompletionRatesTest(BaseTest):
    def setUp(self):
        self.country = LocationType.objects.create(name="Country", slug=slugify("country"))
        self.district = LocationType.objects.create(name="District", slug=slugify("district"))
        self.city = LocationType.objects.create(name="City", slug=slugify("city"))
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.abim = Location.objects.create(name="Abim", type=self.district, tree_parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", type=self.city, tree_parent=self.abim)

        self.zombo = Location.objects.create(name="Zombo", type=self.district, tree_parent=self.uganda)
        self.apachi = Location.objects.create(name="Apachi", type=self.city, tree_parent=self.zombo)

    def test_knows_all_locations_given_type_of_location(self):
        locations = BatchSurveyCompletionRates(self.district).locations
        self.assertIn(self.abim, locations)
        self.assertIn(self.zombo, locations)

        locations = BatchSurveyCompletionRates(self.city).locations
        self.assertIn(self.kampala, locations)
        self.assertIn(self.apachi, locations)


class HouseholdCompletionJsonService(BaseTest):
    def setUp(self):
        self.country = LocationType.objects.create(name="Country", slug=slugify("country"))
        self.district = LocationType.objects.create(name="District", slug=slugify("district"))
        self.city = LocationType.objects.create(name="City", slug=slugify("city"))
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.abim = Location.objects.create(name="Abim", type=self.district, tree_parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", type=self.city, tree_parent=self.abim)

        self.zombo = Location.objects.create(name="Zombo", type=self.district, tree_parent=self.uganda)
        self.apachi = Location.objects.create(name="Apachi", type=self.city, tree_parent=self.zombo)

        self.backend = Backend.objects.create(name='something')
        self.survey = Survey.objects.create(name='SurveyA')
        self.batch = Batch.objects.create(order=1, name='somebatch', survey=self.survey)
        self.batch_2 = Batch.objects.create(order=2, name='somebatch 2', survey=self.survey)

        self.batch.open_for_location(self.abim)
        self.batch.open_for_location(self.zombo)

        self.batch_2.open_for_location(self.abim)
        self.batch_2.open_for_location(self.zombo)

        self.investigator_1 = Investigator.objects.create(name="investigator name_1", mobile_number="9876543210",
                                                          location=self.kampala, backend=self.backend)

        self.investigator_2 = Investigator.objects.create(name="investigator name_2", mobile_number="9876543330",
                                                          location=self.apachi, backend=self.backend)
        self.household_1 = Household.objects.create(investigator=self.investigator_1, location=self.kampala,
                                                    survey=self.survey)
        self.household_2 = Household.objects.create(investigator=self.investigator_1, location=self.kampala,
                                                    survey=self.survey)
        self.household_3 = Household.objects.create(investigator=self.investigator_1, location=self.kampala,
                                                    survey=self.survey)
        self.household_4 = Household.objects.create(investigator=self.investigator_1, location=self.kampala,
                                                    survey=self.survey)

    def test_knows_completion_rates_for_location_type(self):

        household_1_member = HouseholdMember.objects.create(household=self.household_1,
                                                            date_of_birth=date(1980, 05, 01))
        household_2_member = HouseholdMember.objects.create(household=self.household_2,
                                                            date_of_birth=date(1980, 05, 01))
        household_3_member = HouseholdMember.objects.create(household=self.household_3,
                                                            date_of_birth=date(1980, 05, 01))
        household_4_member = HouseholdMember.objects.create(household=self.household_4, date_of_birth=date(1980, 05, 01))

        HouseholdMemberBatchCompletion.objects.create(household=self.household_1, householdmember=household_1_member,
                                                batch=self.batch,
                                                investigator=self.investigator_1)

        HouseholdMemberBatchCompletion.objects.create(household=self.household_2, householdmember=household_2_member,
                                                batch=self.batch,
                                                investigator=self.investigator_1)

        HouseholdMemberBatchCompletion.objects.create(household=self.household_3, householdmember=household_3_member,
                                                batch=self.batch,
                                                investigator=self.investigator_1)

        HouseholdMemberBatchCompletion.objects.create(household=self.household_3, householdmember=household_4_member,
                                                batch=self.batch,
                                                investigator=self.investigator_1)

        self.household_5 = Household.objects.create(investigator=self.investigator_2, location=self.apachi,
                                                    survey=self.survey)
        self.household_6 = Household.objects.create(investigator=self.investigator_2, location=self.apachi,
                                                    survey=self.survey)
        self.household_7 = Household.objects.create(investigator=self.investigator_2, location=self.apachi,
                                                    survey=self.survey)
        self.household_8 = Household.objects.create(investigator=self.investigator_2, location=self.apachi,
                                                    survey=self.survey)

        household_5_member = HouseholdMember.objects.create(household=self.household_5,
                                                            date_of_birth=date(1980, 05, 01))
        household_6_member = HouseholdMember.objects.create(household=self.household_6,
                                                            date_of_birth=date(1980, 05, 01))

        HouseholdMember.objects.create(household=self.household_7, date_of_birth=date(1980, 05, 01))
        HouseholdMember.objects.create(household=self.household_8, date_of_birth=date(1980, 05, 01))

        HouseholdMemberBatchCompletion.objects.create(household=self.household_1, householdmember=household_5_member,
                                                batch=self.batch,
                                                investigator=self.investigator_2)
        HouseholdMemberBatchCompletion.objects.create(household=self.household_2, householdmember=household_6_member,
                                                batch=self.batch,
                                                investigator=self.investigator_2)

        district_level_completion = BatchSurveyCompletionRates(self.district)
        expected_completion = {self.zombo.name: 25.0, self.abim.name: 50.0}
        self.assertEqual(district_level_completion.get_completion_formatted_for_json(self.survey), expected_completion)

    def test_returns_minus_one_when_no_batch_is_open_in_the_location(self):
        kisoro = Location.objects.create(name='Kisoro', type=self.district)

        survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        batch = Batch.objects.create(order=1, name='B', survey=survey)
        batch.open_for_location(self.abim)

        with patch.object(BatchLocationCompletionRates, 'percent_completed_households', return_value=10):
            completion = BatchSurveyCompletionRates(self.district)
            self.assertEqual(-1, completion.get_completion_formatted_for_json(survey)[kisoro.name])
            self.assertNotEqual(0, completion.get_completion_formatted_for_json(survey)[self.abim.name])
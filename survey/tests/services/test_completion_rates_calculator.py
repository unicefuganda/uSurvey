from datetime import date, datetime
from mock import patch
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import Batch, Investigator, Household, Question
from survey.models.households import HouseholdMember
from survey.services.completion_rates_calculator import BatchCompletionRates, BatchLocationCompletionRates, BatchHighLevelLocationsCompletionRates
from survey.tests.base_test import BaseTest


class BatchCompletionRatesTest(BaseTest):
    def setUp(self):
        self.country = LocationType.objects.create(name = 'Country', slug = 'country')
        self.city = LocationType.objects.create(name = 'City', slug = 'city')

        self.uganda = Location.objects.create(name='Uganda', type = self.country)
        self.abim = Location.objects.create(name='Abim', tree_parent = self.uganda, type = self.city)
        self.kampala = Location.objects.create(name='Kampala', tree_parent = self.uganda, type = self.city)
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent = self.kampala, type = self.city)

        self.investigator_1 = Investigator.objects.create(name='some_inv',mobile_number='123456789',male=True,location=self.kampala)
        self.investigator_2 = Investigator.objects.create(name='some_inv',mobile_number='123456788',male=True,location=self.kampala_city)

        self.household_1 = Household.objects.create(investigator = self.investigator_1,location= self.kampala_city)
        self.household_2 = Household.objects.create(investigator = self.investigator_1,location= self.kampala_city)
        self.batch = Batch.objects.create(order=1,name='somebatch')
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
        self.assertEqual(50, completion_rate.percentage_completed(Household.all_households_in(self.investigator_1.location)))
        self.batch.completed_households.create(householdmember=self.member_2)
        self.assertEqual(100, completion_rate.percentage_completed(Household.all_households_in(self.investigator_1.location)))

    def test_percent_completed_households(self):
        completion_rate = BatchCompletionRates(self.batch)
        self.batch.completed_households.create(householdmember=self.member_1)
        self.assertEqual(50, completion_rate.percent_completed_households(self.investigator_1.location))
        self.batch.completed_households.create(householdmember=self.member_2)
        self.assertEqual(100, completion_rate.percent_completed_households(self.investigator_1.location))

    def test_interviewed_households(self):
        completion_rate = BatchLocationCompletionRates(self.batch, self.investigator_1.location)
        batch_member_completion, b = self.member_1.batch_completed(self.batch)
        date_1 = datetime(1999, 2, 4, 23,1,2).replace(tzinfo=batch_member_completion.created.tzinfo)
        batch_member_completion.created= date_1
        batch_member_completion.save()
        interviewed_households = completion_rate.interviewed_households()
        self.assertEqual(2, len(interviewed_households))
        index_of_household_1 = [index for index, interviewed in enumerate(interviewed_households) if interviewed_households[index]['household']==self.household_1]
        interviewed_1 = interviewed_households[index_of_household_1[0]]
        self.assertEqual(date_1.strftime('%d-%b-%Y %H:%M:%S'), interviewed_1['date_interviewed'])
        self.assertEqual(1, interviewed_1['number_of_member_interviewed'])
        interviewed_households.remove(interviewed_1)
        interviewed_2 = interviewed_households[0]
        self.assertEqual(None, interviewed_2['date_interviewed'])
        self.assertEqual(0, interviewed_2['number_of_member_interviewed'])

        batch_member_completion, b= self.member_2.batch_completed(self.batch)

        date_2 = datetime(1997, 2, 4, 23,1,2).replace(tzinfo=batch_member_completion.created.tzinfo)
        batch_member_completion.created= date_2
        batch_member_completion.save()
        interviewed_households = completion_rate.interviewed_households()
        self.assertEqual(2, len(interviewed_households))
        index_of_household_1 = [index for index, interviewed in enumerate(interviewed_households) if interviewed_households[index]['household']==self.household_1]
        interviewed_1 = interviewed_households[index_of_household_1[0]]
        self.assertEqual(date_1.strftime('%d-%b-%Y %H:%M:%S'), interviewed_1['date_interviewed'])
        self.assertEqual(1, interviewed_1['number_of_member_interviewed'])
        interviewed_households.remove(interviewed_1)
        interviewed_2 = interviewed_households[0]
        self.assertEqual(date_2.strftime('%d-%b-%Y %H:%M:%S'), interviewed_2['date_interviewed'])
        self.assertEqual(1, interviewed_2['number_of_member_interviewed'])

    @patch('survey.services.completion_rates_calculator.BatchCompletionRates.percent_completed_households')
    def test_completion_rates(self, mock_percent):
        masaka = Location.objects.create(name="masaka", tree_parent = self.uganda, type = self.city)
        investigator_3 = Investigator.objects.create(name='some_inv_2',mobile_number='123456787',male=True,location=masaka)

        household_3 = Household.objects.create(investigator = investigator_3,location= masaka)
        member_3 = HouseholdMember.objects.create(household=household_3, date_of_birth=date(1980, 05, 01))

        mock_percent.side_effect = lambda location:location.id # return value only needed to change with locations

        completion_rate = BatchHighLevelLocationsCompletionRates(self.batch, [self.kampala_city, masaka])
        completions = completion_rate.attributes()
        self.assertEqual(2, len(completions))
        index_of_kampala_city = [index for index, completion in enumerate(completions) if completions[index]['location']==self.kampala_city]
        completion_1 = completions[index_of_kampala_city[0]]
        self.assertEqual(2, completion_1['total_households'])
        self.assertEqual(self.kampala_city.id, completion_1['completed_households_percent'])

        completions.remove(completion_1)
        completion_2 = completions[0]
        self.assertEqual(1, completion_2['total_households'])
        self.assertEqual(masaka.id, completion_2['completed_households_percent'])

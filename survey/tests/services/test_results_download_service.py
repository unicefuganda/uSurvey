from datetime import date
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Survey, HouseholdMember, Household, Batch, Investigator, Backend, HouseholdMemberGroup, QuestionModule, Question, BatchQuestionOrder, LocationTypeDetails, QuestionOption
from survey.services.results_download_service import ResultsDownloadService
from survey.tests.base_test import BaseTest


class ResultsDownloadServiceTest(BaseTest):
    def setUp(self):
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.county = LocationType.objects.create(name='County', slug='county')
        self.subcounty = LocationType.objects.create(name='Subcounty', slug='subcounty')
        self.parish = LocationType.objects.create(name='Parish', slug='parish')
        self.village = LocationType.objects.create(name='Village', slug='village')

        uganda = Location.objects.create(name="Uganda", type=self.country)

        LocationTypeDetails.objects.create(country=uganda, location_type=self.country)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.district)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.county)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.subcounty)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.parish)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.village)

        self.survey = Survey.objects.create(name='survey name', description='survey descrpition', type=False,
                                            sample_size=10)
        self.kampala = Location.objects.create(name="Kampala", type=self.district, tree_parent=uganda)
        self.batch = Batch.objects.create(order=1, name="Batch A", survey=self.survey)
        backend = Backend.objects.create(name='something')
        self.investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=self.kampala,
                                                        backend=backend)

        group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        module = QuestionModule.objects.create(name="Education")
        self.question_1 = Question.objects.create(group=group, text="Question 1", module=module,
                                                  answer_type=Question.NUMBER,
                                                  order=1, identifier='Q1')
        self.question_2 = Question.objects.create(group=group, text="Question 2", module=module,
                                                  answer_type=Question.MULTICHOICE,
                                                  order=2, identifier='Q2')
        self.question_3 = Question.objects.create(group=group, text="Question 3", module=module,
                                                  answer_type=Question.NUMBER,
                                                  order=3, identifier='Q3')

        self.yes_option = QuestionOption.objects.create(question=self.question_2, text="Yes", order=1)
        self.no_option = QuestionOption.objects.create(question=self.question_2, text="No", order=2)


        self.question_1.batches.add(self.batch)
        self.question_2.batches.add(self.batch)
        self.question_3.batches.add(self.batch)

        BatchQuestionOrder.objects.create(question=self.question_1, batch=self.batch, order=1)
        BatchQuestionOrder.objects.create(question=self.question_2, batch=self.batch, order=2)
        BatchQuestionOrder.objects.create(question=self.question_3, batch=self.batch, order=3)

    def test_formats_headers_for_csv_leaving_out_country(self):
        result_down_load_service = ResultsDownloadService(self.batch)
        header_structure = [self.district.name, self.county.name, self.subcounty.name, self.parish.name,
                            self.village.name,
                            'Household ID', 'Name', 'Age', 'Month of Birth', 'Year of Birth', 'Gender',
                            self.question_1.identifier,
                            self.question_2.identifier, '', self.question_3.identifier]

        headers = result_down_load_service.set_report_headers()
        self.assertEqual(header_structure, headers)

    def test_gets_summarised_response_for_a_given_batch(self):
        household_head_1 = self.create_household_head(0, self.investigator, self.batch.survey)
        household_head_2 = self.create_household_head(1, self.investigator, self.batch.survey)
        household_head_3 = self.create_household_head(2, self.investigator, self.batch.survey)
        household_head_4 = self.create_household_head(3, self.investigator, self.batch.survey)
        household_head_5 = self.create_household_head(4, self.investigator, self.batch.survey)

        self.investigator.member_answered(self.question_1, household_head_1, 1, self.batch)
        self.investigator.member_answered(self.question_1, household_head_2, 2, self.batch)
        self.investigator.member_answered(self.question_1, household_head_3, 1, self.batch)
        self.investigator.member_answered(self.question_1, household_head_4, 2, self.batch)
        self.investigator.member_answered(self.question_1, household_head_5, 3, self.batch)

        self.investigator.member_answered(self.question_2, household_head_1, self.no_option.order, self.batch)
        self.investigator.member_answered(self.question_2, household_head_2, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_2, household_head_3, self.no_option.order, self.batch)
        self.investigator.member_answered(self.question_2, household_head_4, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_2, household_head_5, self.yes_option.order, self.batch)

        self.investigator.member_answered(self.question_3, household_head_1, 1, self.batch)
        self.investigator.member_answered(self.question_3, household_head_2, 2, self.batch)
        self.investigator.member_answered(self.question_3, household_head_3, 1, self.batch)
        self.investigator.member_answered(self.question_3, household_head_4, 2, self.batch)
        self.investigator.member_answered(self.question_3, household_head_5, 3, self.batch)

        result_down_load_service = ResultsDownloadService(self.batch)
        expected_csv_data = [['Kampala', household_head_1.household.household_code, household_head_1.surname, '23', '2',  '1990',
                             'Male' if household_head_1.male else 'Female',  1, self.no_option.order, self.no_option.text,  1],
                             ['Kampala', household_head_2.household.household_code, household_head_2.surname, '23', '2',  '1990',
                             'Male' if household_head_2.male else 'Female',  2, self.yes_option.order, self.yes_option.text,  2],
                             ['Kampala', household_head_3.household.household_code, household_head_3.surname, '23', '2',  '1990',
                             'Male' if household_head_3.male else 'Female',  1, self.no_option.order, self.no_option.text,  1],
                             ['Kampala', household_head_4.household.household_code, household_head_4.surname, '23', '2',  '1990',
                             'Male' if household_head_4.male else 'Female',  2, self.yes_option.order, self.yes_option.text,  2],
                             ['Kampala', household_head_5.household.household_code, household_head_5.surname, '23', '2',  '1990',
                             'Male' if household_head_5.male else 'Female',  3, self.yes_option.order, self.yes_option.text,  3]]

        actual_csv_data = result_down_load_service.get_summarised_answers()
        self.assertEqual(5, len(actual_csv_data))
        for i in range(5):
            self.assertIn(expected_csv_data[i], actual_csv_data)

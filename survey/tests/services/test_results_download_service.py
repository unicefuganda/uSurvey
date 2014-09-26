from datetime import date
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Survey, HouseholdMember, Batch, Investigator, Backend, HouseholdMemberGroup, QuestionModule, Question, BatchQuestionOrder, LocationTypeDetails, QuestionOption, GroupCondition, EnumerationArea
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
        self.ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
        self.ea.locations.add(self.kampala)
        self.investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", ea=self.ea,
                                                        backend=backend)

        self.group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        general_condition = GroupCondition.objects.create(attribute="GENDER", value=False, condition='EQUALS')
        self.group.conditions.add(general_condition)

        module = QuestionModule.objects.create(name="Education")
        self.question_1 = Question.objects.create(group=self.group, text="Question 1", module=module,
                                                  answer_type=Question.NUMBER,
                                                  order=1, identifier='Q1')
        self.question_2 = Question.objects.create(group=self.group, text="Question 2", module=module,
                                                  answer_type=Question.MULTICHOICE,
                                                  order=2, identifier='Q2')
        self.question_3 = Question.objects.create(group=self.group, text="Question 3", module=module,
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
        result_down_load_service = ResultsDownloadService(batch=self.batch)
        header_structure = [self.district.name, self.county.name, self.subcounty.name, self.parish.name,
                            self.village.name,
                            'Household ID', 'Name', 'Age', 'Month of Birth', 'Year of Birth', 'Gender',
                            self.question_1.identifier,
                            self.question_2.identifier, '', self.question_3.identifier]

        headers = result_down_load_service.set_report_headers()
        self.assertEqual(header_structure, headers)

    def test_gets_summarised_response_for_a_given_batch(self):
        HouseholdMemberGroup.objects.create(name="GENERAL", order=2)
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

        result_down_load_service = ResultsDownloadService(batch=self.batch)
        AGE = '24'
        expected_csv_data = [
            ['Kampala', household_head_1.household.household_code, household_head_1.surname, AGE, '2', '1990',
             'Male' if household_head_1.male else 'Female', 1, self.no_option.order, self.no_option.text, 1],
            ['Kampala', household_head_2.household.household_code, household_head_2.surname, AGE, '2', '1990',
             'Male' if household_head_2.male else 'Female', 2, self.yes_option.order, self.yes_option.text, 2],
            ['Kampala', household_head_3.household.household_code, household_head_3.surname, AGE, '2', '1990',
             'Male' if household_head_3.male else 'Female', 1, self.no_option.order, self.no_option.text, 1],
            ['Kampala', household_head_4.household.household_code, household_head_4.surname, AGE, '2', '1990',
             'Male' if household_head_4.male else 'Female', 2, self.yes_option.order, self.yes_option.text, 2],
            ['Kampala', household_head_5.household.household_code, household_head_5.surname, AGE, '2', '1990',
             'Male' if household_head_5.male else 'Female', 3, self.yes_option.order, self.yes_option.text, 3]]

        actual_csv_data = result_down_load_service.get_summarised_answers()
        self.assertEqual(5, len(actual_csv_data))
        for i in range(5):
            self.assertIn(expected_csv_data[i], actual_csv_data)

    def test_should_repeat_questions_in_general_for_all_members(self):
        AGE = '24'
        general_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=2)

        general_condition = GroupCondition.objects.create(attribute="GENERAL", value="HEAD", condition='EQUALS')
        general_group.conditions.add(general_condition)

        general_question_1 = Question.objects.create(group=general_group, text="General Question 1",
                                                     answer_type=Question.NUMBER,
                                                     order=4, identifier='Q31')
        general_question_2 = Question.objects.create(group=general_group, text="General Question 2",
                                                     answer_type=Question.NUMBER,
                                                     order=5, identifier='Q41')

        general_question_1.batches.add(self.batch)
        general_question_2.batches.add(self.batch)

        BatchQuestionOrder.objects.create(question=general_question_1, batch=self.batch, order=4)
        BatchQuestionOrder.objects.create(question=general_question_2, batch=self.batch, order=5)

        household_head_1 = self.create_household_head(0, self.investigator, self.batch.survey)
        household_head_2 = self.create_household_head(1, self.investigator, self.batch.survey)

        member_1 = HouseholdMember.objects.create(surname="Member 1", date_of_birth=date(1999, 2, 9),
                                                  household=household_head_1.household)
        member_2 = HouseholdMember.objects.create(surname="Member 2", date_of_birth=date(1999, 2, 9),
                                                  household=household_head_2.household)

        self.investigator.member_answered(self.question_1, household_head_1, 1, self.batch)
        self.investigator.member_answered(self.question_1, household_head_2, 2, self.batch)

        self.investigator.member_answered(general_question_1, household_head_1, 4, self.batch)
        self.investigator.member_answered(general_question_1, household_head_2, 1, self.batch)

        self.investigator.member_answered(general_question_2, household_head_1, 4, self.batch)
        self.investigator.member_answered(general_question_2, household_head_2, 3, self.batch)

        self.investigator.member_answered(self.question_2, household_head_1, self.no_option.order, self.batch)
        self.investigator.member_answered(self.question_2, household_head_2, self.yes_option.order, self.batch)

        self.investigator.member_answered(self.question_3, household_head_1, 1, self.batch)
        self.investigator.member_answered(self.question_3, household_head_2, 2, self.batch)

        result_down_load_service = ResultsDownloadService(batch=self.batch)
        age = '24'
        age_14 = '15'
        expected_csv_data = [
            ['Kampala', household_head_1.household.household_code, household_head_1.surname, age, '2', '1990',
             'Male' if household_head_1.male else 'Female', 1, self.no_option.order, self.no_option.text, 1, 4, 4],
            ['Kampala', household_head_2.household.household_code, member_1.surname, age_14, '2', '1999',
             'Male' if member_1.male else 'Female', '', '', '', 4, 4],
            ['Kampala', household_head_2.household.household_code, household_head_2.surname, age, '2', '1990',
             'Male' if household_head_2.male else 'Female', 2, self.yes_option.order, self.yes_option.text, 2, 1, 3],
            ['Kampala', household_head_2.household.household_code, member_2.surname, age_14, '2', '1999',
             'Male' if member_2.male else 'Female', '', '', '', 1, 3]]

        actual_csv_data = result_down_load_service.get_summarised_answers()
        self.assertEqual(4, len(actual_csv_data))
        for i in range(4):
            self.assertIn(expected_csv_data[i], actual_csv_data)
            
    def test_gets_summarised_response_for_all_batches_under_survey(self):
        HouseholdMemberGroup.objects.create(name="GENERAL", order=2)
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

        batchB = Batch.objects.create(order=2, name="different batch", survey=self.survey)
        module = QuestionModule.objects.create(name="Education in a different batch")
        question_1B = Question.objects.create(group=self.group, text="Question 1 B", module=module,
                                                  answer_type=Question.NUMBER,
                                                  order=1, identifier='Q1B')
        question_2B = Question.objects.create(group=self.group, text="Question 2B", module=module,
                                                  answer_type=Question.MULTICHOICE,
                                                  order=2, identifier='Q2B')
        question_3B = Question.objects.create(group=self.group, text="Question 3B", module=module,
                                                  answer_type=Question.NUMBER,
                                                  order=3, identifier='Q3B')

        yes_option = QuestionOption.objects.create(question=question_2B, text="Yes", order=1)
        no_option = QuestionOption.objects.create(question=question_2B, text="No", order=2)

        question_1B.batches.add(batchB)
        question_2B.batches.add(batchB)
        question_3B.batches.add(batchB)

        BatchQuestionOrder.objects.create(question=question_1B, batch=batchB, order=1)
        BatchQuestionOrder.objects.create(question=question_2B, batch=batchB, order=2)
        BatchQuestionOrder.objects.create(question=question_3B, batch=batchB, order=3)

        self.investigator.member_answered(question_1B, household_head_1, 1, batchB)
        self.investigator.member_answered(question_1B, household_head_2, 2, batchB)
        self.investigator.member_answered(question_1B, household_head_3, 1, batchB)
        self.investigator.member_answered(question_1B, household_head_4, 2, batchB)
        self.investigator.member_answered(question_1B, household_head_5, 3, batchB)

        self.investigator.member_answered(question_2B, household_head_1, no_option.order, batchB)
        self.investigator.member_answered(question_2B, household_head_2, yes_option.order, batchB)
        self.investigator.member_answered(question_2B, household_head_3, no_option.order, batchB)
        self.investigator.member_answered(question_2B, household_head_4, yes_option.order, batchB)
        self.investigator.member_answered(question_2B, household_head_5, yes_option.order, batchB)

        self.investigator.member_answered(question_3B, household_head_1, 1, batchB)
        self.investigator.member_answered(question_3B, household_head_2, 2, batchB)
        self.investigator.member_answered(question_3B, household_head_3, 1, batchB)
        self.investigator.member_answered(question_3B, household_head_4, 2, batchB)
        self.investigator.member_answered(question_3B, household_head_5, 3, batchB)

        result_down_load_service = ResultsDownloadService(survey=self.survey)

        header_structure = [self.district.name, self.county.name, self.subcounty.name, self.parish.name,
                            self.village.name,
                            'Household ID', 'Name', 'Age', 'Month of Birth', 'Year of Birth', 'Gender',
                            self.question_1.identifier, self.question_2.identifier, '', self.question_3.identifier,
                            question_1B.identifier, question_2B.identifier, '', question_3B.identifier]

        headers = result_down_load_service.set_report_headers()
        self.assertEqual(header_structure, headers)

        age = '24'
        expected_csv_data = [
            ['Kampala', household_head_1.household.household_code, household_head_1.surname, age, '2', '1990',
             'Male' if household_head_1.male else 'Female', 1, self.no_option.order, self.no_option.text, 1,
            1, no_option.order, no_option.text, 1],
            ['Kampala', household_head_2.household.household_code, household_head_2.surname, age, '2', '1990',
             'Male' if household_head_2.male else 'Female', 2, self.yes_option.order, self.yes_option.text, 2,
             2, yes_option.order, yes_option.text, 2],
            ['Kampala', household_head_3.household.household_code, household_head_3.surname, age, '2', '1990',
             'Male' if household_head_3.male else 'Female', 1, self.no_option.order, self.no_option.text, 1,
             1, no_option.order, no_option.text, 1],
            ['Kampala', household_head_4.household.household_code, household_head_4.surname, age, '2', '1990',
             'Male' if household_head_4.male else 'Female', 2, self.yes_option.order, self.yes_option.text, 2,
             2, yes_option.order, yes_option.text, 2],
            ['Kampala', household_head_5.household.household_code, household_head_5.surname, age, '2', '1990',
             'Male' if household_head_5.male else 'Female', 3, self.yes_option.order, self.yes_option.text, 3,
             3, yes_option.order, yes_option.text, 3]]

        actual_csv_data = result_down_load_service.get_summarised_answers()
        self.assertEqual(5, len(actual_csv_data))
        for i in range(5):
            self.assertIn(expected_csv_data[i], actual_csv_data)
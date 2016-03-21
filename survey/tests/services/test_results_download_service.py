from datetime import date
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models.locations import *
from survey.models import Survey, HouseholdMember, Batch, Interviewer, Backend, HouseholdMemberGroup, \
    QuestionModule, Question, LocationTypeDetails, QuestionOption, GroupCondition, EnumerationArea, \
    HouseholdListing, SurveyHouseholdListing, Household
from survey.services.results_download_service import ResultsDownloadService
from survey.tests.base_test import BaseTest
from survey.features.simple_indicator_chart_step import create_household_head


class ResultsDownloadServiceTest(BaseTest):
    def setUp(self):
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.district = LocationType.objects.create(name='District', slug='district', parent=self.country)
        self.county = LocationType.objects.create(name='County', slug='county', parent=self.district)
        self.subcounty = LocationType.objects.create(name='Subcounty', slug='subcounty', parent=self.county)
        self.parish = LocationType.objects.create(name='Parish', slug='parish', parent=self.subcounty)
        self.village = LocationType.objects.create(name='Village', slug='village', parent=self.parish)

        uganda = Location.objects.create(name="Uganda", type=self.country)

        LocationTypeDetails.objects.create(country=uganda, location_type=self.country)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.district)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.county)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.subcounty)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.parish)
        LocationTypeDetails.objects.create(country=uganda, location_type=self.village)

        self.survey = Survey.objects.create(name='survey name', description='survey descrpition',
                                            sample_size=10)
        self.kampala = Location.objects.create(name="Kampala", type=self.district, parent=uganda)
        self.batch = Batch.objects.create(order=1, name="Batch A", survey=self.survey)
        backend = Backend.objects.create(name='something')
        self.ea = EnumerationArea.objects.create(name="EA")
        self.ea.locations.add(self.kampala)
        self.investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=self.ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)

        self.group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        general_condition = GroupCondition.objects.create(attribute="GENDER", value=False, condition='EQUALS')
        self.group.conditions.add(general_condition)

        module = QuestionModule.objects.create(name="Education")
        self.question_1 = Question.objects.create(identifier='1.11',text="This is a question11", answer_type='Numerical Answer',
                                           group=self.group,batch=self.batch,module=module)
        self.question_2 = Question.objects.create(identifier='1.12',text="This is a question12", answer_type='Numerical Answer',
                                           group=self.group,batch=self.batch,module=module)
        self.question_3 = Question.objects.create(identifier='1.13',text="This is a question13", answer_type='Numerical Answer',
                                           group=self.group,batch=self.batch,module=module)

        self.yes_option = QuestionOption.objects.create(question=self.question_2, text="Yes", order=1)
        self.no_option = QuestionOption.objects.create(question=self.question_2, text="No", order=2)

        # self.question_1.batches.add(self.batch)
        # self.question_2.batches.add(self.batch)
        # self.question_3.batches.add(self.batch)

        # BatchQuestionOrder.objects.create(question=self.question_1, batch=self.batch, order=1)
        # BatchQuestionOrder.objects.create(question=self.question_2, batch=self.batch, order=2)
        # BatchQuestionOrder.objects.create(question=self.question_3, batch=self.batch, order=3)

    def test_formats_headers_for_csv_leaving_out_country(self):
        result_down_load_service = ResultsDownloadService(batch=self.batch)
        header_structure = [unicode(self.district.name), unicode(self.county.name), unicode(self.subcounty.name), unicode(self.parish.name),
                            unicode(self.village.name),unicode(self.ea.name),
                            'Household Number', 'Family Name', 'First Name', 'Age', 'Date of Birth', 'Gender'
                            ]
        headers = result_down_load_service.set_report_headers()
        self.assertEqual(header_structure, headers)

    def test_gets_summarised_response_for_a_given_batch(self):
        household_listing = HouseholdListing.objects.create(ea=self.ea,list_registrar=self.investigator,initial_survey=self.survey)
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=self.survey)
        HouseholdMemberGroup.objects.create(name="GENERAL", order=2)
        household_head_1 = create_household_head(0, self.investigator,household_listing,survey_householdlisting)
        household_head_2 = create_household_head(1, self.investigator,household_listing,survey_householdlisting)
        household_head_3 = create_household_head(2, self.investigator,household_listing,survey_householdlisting)
        household_head_4 = create_household_head(3, self.investigator,household_listing,survey_householdlisting)
        household_head_5 = create_household_head(4, self.investigator,household_listing,survey_householdlisting)
        result_down_load_service = ResultsDownloadService(batch=self.batch)
        AGE = '28'
        household1=household_head_1.surname+'-'+household_head_1.first_name
        household2=household_head_2.surname+'-'+household_head_2.first_name
        household3=household_head_3.surname+'-'+household_head_3.first_name
        household4=household_head_4.surname+'-'+household_head_4.first_name
        household5=household_head_5.surname+'-'+household_head_5.first_name
        expected_csv_data = [
            [u'Kampala', unicode(self.ea.name), household_head_1.household.house_number,unicode(household1),AGE, '01-01-1988',
             'Male' if household_head_1.household.head_sex else 'Female'],
            [u'Kampala', unicode(self.ea.name),household_head_2.household.house_number, unicode(household2), AGE, '01-01-1988',
             'Male' if household_head_2.household.head_sex else 'Female'],
            [u'Kampala', unicode(self.ea.name),household_head_3.household.house_number, unicode(household3), AGE, '01-01-1988',
             'Male' if household_head_3.household.head_sex else 'Female'],
            [u'Kampala', unicode(self.ea.name),household_head_4.household.house_number, unicode(household4),AGE, '01-01-1988',
             'Male' if household_head_4.household.head_sex else 'Female'],
            [u'Kampala', unicode(self.ea.name),household_head_5.household.house_number, unicode(household5),AGE, '01-01-1988',
             'Male' if household_head_5.household.head_sex else 'Female']]
        batch = Batch.objects.create(name="Batch name", description='description')
        group_1 = HouseholdMemberGroup.objects.create(name="Group 11", order=10)
        group_2 = HouseholdMemberGroup.objects.create(name="Group 12", order=11)
        group_3 = HouseholdMemberGroup.objects.create(name="Group 13", order=12)
        household_member_group = HouseholdMemberGroup.objects.create(name="Greater than 65 years", order=19)
        question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        question_1 = Question.objects.create(identifier='1.1',text="This is a question1", answer_type='Numerical Answer',
                                            group=group_3,batch=batch,module=question_mod)
        actual_csv_data = result_down_load_service.get_summarised_answers()
        self.assertEqual(5, len(actual_csv_data))
        for i in range(5):
            self.assertIn(expected_csv_data[i], actual_csv_data)

    def test_should_repeat_questions_in_general_for_all_members(self):
        household_listing1 = HouseholdListing.objects.create(ea=self.ea,list_registrar=self.investigator,initial_survey=self.survey)
        survey_householdlisting1 = SurveyHouseholdListing.objects.create(listing=household_listing1,survey=self.survey)
        AGE = '24'
        general_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=2)

        general_condition = GroupCondition.objects.create(attribute="GENERAL", value="HEAD", condition='EQUALS')
        general_group.conditions.add(general_condition)
        module1 = QuestionModule.objects.create(name="Education123")
        general_question_1 = Question.objects.create(identifier='1.111',text="This is a question111", answer_type='Numerical Answer',
                                           group=self.group,batch=self.batch,module=module1)
        general_question_2 = Question.objects.create(identifier='1.112',text="This is a question112", answer_type='Numerical Answer',
                                           group=self.group,batch=self.batch,module=module1)
        ea = EnumerationArea.objects.create(name="EA")
        ea.locations.add(self.kampala)
        household_head_1 = create_household_head(0, self.investigator,household_listing1,survey_householdlisting1)
        household_head_2 = create_household_head(1, self.investigator,household_listing1,survey_householdlisting1)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=self.investigator,initial_survey=self.survey)
        household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=self.survey)
        member_1 = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household_head_1.household,survey_listing=survey_householdlisting,
                                                          registrar=self.investigator,registration_channel="ODK Access")
        member_2 = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household_head_2.household,survey_listing=survey_householdlisting,
                                                          registrar=self.investigator,registration_channel="ODK Access")
        result_down_load_service = ResultsDownloadService(batch=self.batch)
        age = '28'
        age_14 = '15'
        household1=household_head_1.surname+'-'+household_head_1.first_name
        member1=member_1.surname+'-'+member_1.first_name
        household2=household_head_2.surname+'-'+household_head_2.first_name
        expected_csv_data = [
            [u'Kampala',unicode(ea.name), household_head_1.household.house_number, household1, age,  '01-01-1988',
             'Male' if household_head_1.household.head_sex else 'Female'],
            [u'Kampala' ,unicode(ea.name), household_head_2.household.house_number, household2, age, '01-01-1988',
             'Male' if household_head_2.household.head_sex else 'Female']]

        actual_csv_data = result_down_load_service.get_summarised_answers()
        self.assertEqual(4, len(actual_csv_data))
        for i in range(2):
            self.assertIn(expected_csv_data[i], actual_csv_data)

    def test_gets_summarised_response_for_all_batches_under_survey(self):
        household_listing = HouseholdListing.objects.create(ea=self.ea,list_registrar=self.investigator,initial_survey=self.survey)
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=self.survey)
        HouseholdMemberGroup.objects.create(name="GENERAL", order=2)
        household_head_1 = create_household_head(0, self.investigator,household_listing,survey_householdlisting)
        household_head_2 = create_household_head(1, self.investigator,household_listing,survey_householdlisting)
        household_head_3 = create_household_head(2, self.investigator,household_listing,survey_householdlisting)
        household_head_4 = create_household_head(3, self.investigator,household_listing,survey_householdlisting)
        household_head_5 = create_household_head(4, self.investigator,household_listing,survey_householdlisting)

        batchB = Batch.objects.create(order=2, name="different batch", survey=self.survey)
        module = QuestionModule.objects.create(name="Education in a different batch")
        question_1B = Question.objects.create(identifier='1.21',text="This is a question21", answer_type='Numerical Answer',
                                           group=self.group,batch=self.batch,module=module)
        question_2B = Question.objects.create(identifier='1.22',text="This is a question22", answer_type='Numerical Answer',
                                           group=self.group,batch=self.batch,module=module)
        question_3B = Question.objects.create(identifier='1.23',text="This is a question23", answer_type='Numerical Answer',
                                           group=self.group,batch=self.batch,module=module)

        yes_option = QuestionOption.objects.create(question=question_2B, text="Yes", order=1)
        no_option = QuestionOption.objects.create(question=question_2B, text="No", order=2)

        result_down_load_service = ResultsDownloadService(survey=self.survey)

        header_structure = [unicode(self.district.name), unicode(self.county.name), unicode(self.subcounty.name), unicode(self.parish.name),
                            unicode(self.village.name), unicode(self.ea.name),
                            'Household Number', 'Family Name', 'First Name','Age', 'Date of Birth', 'Gender']

        headers = result_down_load_service.set_report_headers()
        self.assertEqual(header_structure, headers)

        AGE = '28'
        household1=household_head_1.surname+'-'+household_head_1.first_name
        household2=household_head_2.surname+'-'+household_head_2.first_name
        household3=household_head_3.surname+'-'+household_head_3.first_name
        household4=household_head_4.surname+'-'+household_head_4.first_name
        household5=household_head_5.surname+'-'+household_head_5.first_name
        expected_csv_data = [

            [u'Kampala', unicode(self.ea.name),household_head_2.household.house_number, unicode(household2), AGE, '01-01-1988',
             'Male' if household_head_2.household.head_sex else 'Female'],
            [u'Kampala', unicode(self.ea.name),household_head_3.household.house_number, unicode(household3), AGE, '01-01-1988',
             'Male' if household_head_3.household.head_sex else 'Female'],
            [u'Kampala', unicode(self.ea.name),household_head_4.household.house_number, unicode(household4),AGE, '01-01-1988',
             'Male' if household_head_4.household.head_sex else 'Female'],
            [u'Kampala', unicode(self.ea.name),household_head_5.household.house_number, unicode(household5),AGE, '01-01-1988',
             'Male' if household_head_5.household.head_sex else 'Female']]

        actual_csv_data = result_down_load_service.get_summarised_answers()
        self.assertEqual(5, len(actual_csv_data))
        for i in range(4):
            self.assertIn(expected_csv_data[i], actual_csv_data)
from random import randint
from survey.models.locations import *
from survey.models import Backend, Interviewer, QuestionModule, Question, QuestionOption, Indicator, Formula, \
    Household, HouseholdHead, Batch, MultiChoiceAnswer, HouseholdMemberGroup, Survey, GroupCondition, EnumerationArea, HouseholdListing, \
    SurveyHouseholdListing
from survey.services.simple_indicator_service import SimpleIndicatorService
from survey.tests.base_test import BaseTest
from survey.features.simple_indicator_chart_step import create_household_head

class MultiChoiceQuestionSimpleIndicatorServiceTest(BaseTest):
    def setUp(self):
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1)
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.region = LocationType.objects.create(name="Region", slug="region", parent=self.country)
        self.district = LocationType.objects.create(name="District", slug='district', parent=self.region)

        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.west = Location.objects.create(name="WEST", type=self.region, parent=self.uganda)
        self.central = Location.objects.create(name="CENTRAL", type=self.region, parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", parent=self.west, type=self.district)
        self.ea = EnumerationArea.objects.create(name="EA2")
        self.ea.locations.add(self.kampala)
        self.mbarara_ea = EnumerationArea.objects.create(name="EA3")
        self.mbarara_ea.locations.add(self.mbarara)


        backend = Backend.objects.create(name='something')

        self.investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=self.ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        self.investigator_2 = Interviewer.objects.create(name="Investigator123",
                                                   ea=self.ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)

        health_module = QuestionModule.objects.create(name="Health")
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.question_3 = Question.objects.create(identifier='1.11',text="This is a question11", answer_type='Numerical Answer',
                                           group=member_group,batch=self.batch,module=health_module)
        self.yes_option = QuestionOption.objects.create(question=self.question_3, text="Yes", order=1)
        self.no_option = QuestionOption.objects.create(question=self.question_3, text="No", order=2)

        # self.question_3.batches.add(self.batch)

        self.indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
                                             batch=self.batch, module=health_module)
        self.formula = Formula.objects.create(count=self.question_3, indicator=self.indicator)
        self.household_listing = HouseholdListing.objects.create(ea=self.ea,list_registrar=self.investigator,initial_survey=self.survey)
        self.survey_householdlisting = SurveyHouseholdListing.objects.create(listing=self.household_listing,survey=self.survey)
        self.household_head_1 = create_household_head(0, self.investigator,self.household_listing,self.survey_householdlisting)
        self.household_head_2 = create_household_head(1, self.investigator,self.household_listing,self.survey_householdlisting)
        self.household_head_3 = create_household_head(2, self.investigator,self.household_listing,self.survey_householdlisting)
        self.household_head_4 = create_household_head(3, self.investigator,self.household_listing,self.survey_householdlisting)
        self.household_head_5 = create_household_head(4, self.investigator,self.household_listing,self.survey_householdlisting)

        self.household_head_6 = create_household_head(5, self.investigator_2,self.household_listing,self.survey_householdlisting)
        self.household_head_7 = create_household_head(6, self.investigator_2,self.household_listing,self.survey_householdlisting)
        self.household_head_8 = create_household_head(7, self.investigator_2,self.household_listing,self.survey_householdlisting)
        self.household_head_9 = create_household_head(8, self.investigator_2,self.household_listing,self.survey_householdlisting)

    def test_gets_location_names_and_data_series_for_a_parent_location_and_formula(self):
        simple_indicator_service = SimpleIndicatorService(self.formula, self.uganda)
        region_responses = [{'data': [0, 0], 'name': self.yes_option.text}, {'data': [0, 0], 'name': self.no_option.text}]
        data_series, location = simple_indicator_service.get_location_names_and_data_series()
        self.assertEquals([self.central.name, self.west.name],  location)
        self.assertEquals(region_responses,  data_series)

    def test_formats_details_data(self):
        kibungo = Location.objects.create(name="Kibungo", type=self.district, parent=self.west)
        mpigi = Location.objects.create(name="Mpigi", type=self.district, parent=self.central)
        table_row_1 = {'Region': self.central.name, 'District': self.kampala.name, self.yes_option.text: 3, self.no_option.text: 2,'Total': 5}
        table_row_2 = {'Region': self.central.name, 'District': mpigi.name, self.yes_option.text: 0, self.no_option.text: 0,'Total': 0}
        table_row_3 = {'Region': self.west.name, 'District': kibungo.name, self.yes_option.text: 0, self.no_option.text: 0,'Total': 0}
        table_row_4 = {'Region': self.west.name, 'District': self.mbarara.name, self.yes_option.text: 2, self.no_option.text: 2,'Total': 4}
        expected_table_data = [table_row_1, table_row_2, table_row_3, table_row_4]

        simple_indicator_service = SimpleIndicatorService(self.formula, self.uganda)
        tabulated_data = simple_indicator_service.tabulated_data_series()

        self.assertEqual(4, len(tabulated_data))

class GroupCountSimpleIndicatorServiceTest(BaseTest):
    def setUp(self):
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1, survey=self.survey)
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.region = LocationType.objects.create(name="Region", slug="region", parent=self.country)
        self.district = LocationType.objects.create(name="District", slug='district', parent=self.region)

        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.west = Location.objects.create(name="WEST", type=self.region, parent=self.uganda)
        self.central = Location.objects.create(name="CENTRAL", type=self.region, parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", parent=self.west, type=self.district)
        self.ea = EnumerationArea.objects.create(name="EA2")
        self.ea.locations.add(self.kampala)
        self.mbarara_ea = EnumerationArea.objects.create(name="EA3")
        self.mbarara_ea.locations.add(self.mbarara)

        backend = Backend.objects.create(name='something')

        health_module = QuestionModule.objects.create(name="Health")
        self.investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=self.ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        self.investigator_2 = Interviewer.objects.create(name="Investigator",
                                                   ea=self.mbarara_ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)

        self.general_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=2)

        general_condition = GroupCondition.objects.create(attribute="GENERAL", value="HEAD", condition='EQUALS')
        self.general_group.conditions.add(general_condition)
        self.household_listing = HouseholdListing.objects.create(ea=self.ea,list_registrar=self.investigator,initial_survey=self.survey)
        self.survey_householdlisting = SurveyHouseholdListing.objects.create(listing=self.household_listing,survey=self.survey)
        self.household_head_1 = create_household_head(0, self.investigator,self.household_listing,self.survey_householdlisting)
        self.household_head_2 = create_household_head(1, self.investigator,self.household_listing,self.survey_householdlisting)
        self.household_head_3 = create_household_head(2, self.investigator,self.household_listing,self.survey_householdlisting)
        self.household_head_4 = create_household_head(3, self.investigator,self.household_listing,self.survey_householdlisting)
        self.household_head_5 = create_household_head(4, self.investigator,self.household_listing,self.survey_householdlisting)

        self.household_head_6 = create_household_head(5, self.investigator_2,self.household_listing,self.survey_householdlisting)
        self.household_head_7 = create_household_head(6, self.investigator_2,self.household_listing,self.survey_householdlisting)
        self.household_head_8 = create_household_head(7, self.investigator_2,self.household_listing,self.survey_householdlisting)
        self.household_head_9 = create_household_head(8, self.investigator_2,self.household_listing,self.survey_householdlisting)

        self.indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
                                             module=health_module, batch=self.batch)
        self.question_1 = Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
                                           group=self.general_group,batch=self.batch,module=health_module)
        self.question_2 = Question.objects.create(identifier='1.2',text="How many of them are male?",
                                             answer_type="Numerical Answer", group=self.general_group,batch=self.batch,
                                             module=health_module)

        self.option1 = QuestionOption.objects.create(question=self.question_1, text="This is an option1",order=1)
        self.option2 = QuestionOption.objects.create(question=self.question_2, text="This is an option2",order=2)
        self.formula = Formula.objects.create(numerator=self.question_1, groups=self.general_group,denominator=self.question_2,
                                         count=self.question_1, indicator=self.indicator)

    def test_gets_location_names_and_data_series_for_a_parent_location_and_formula(self):
        simple_indicator_service = SimpleIndicatorService(self.formula, self.uganda)
        region_responses = [{'data': [0, 0], 'name': 'This is an option1'}]
        data_series, location = simple_indicator_service.get_location_names_and_data_series()
        self.assertEquals([self.central.name, self.west.name],  location)
        self.assertEquals(region_responses,  data_series)

    def test_formats_details_data(self):
        kibungo = Location.objects.create(name="Kibungo", type=self.district, parent=self.west)
        mpigi = Location.objects.create(name="Mpigi", type=self.district, parent=self.central)
        table_row_1 = {'Region': self.central.name, 'District': self.kampala.name, self.general_group.name: 5, 'Total': 5}
        table_row_2 = {'Region': self.central.name, 'District': mpigi.name, self.general_group.name: 0, 'Total': 0}
        table_row_3 = {'Region': self.west.name, 'District': kibungo.name, self.general_group.name: 0, 'Total': 0}
        table_row_4 = {'Region': self.west.name, 'District': self.mbarara.name, self.general_group.name: 4, 'Total': 4}
        expected_table_data = [table_row_1, table_row_2, table_row_3, table_row_4]

        simple_indicator_service = SimpleIndicatorService(self.formula, self.uganda)
        tabulated_data = simple_indicator_service.tabulated_data_series()

        self.assertEqual(4, len(tabulated_data))

from random import randint
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Backend, Investigator, QuestionModule, Question, QuestionOption, Indicator, Formula, Household, HouseholdHead, Batch, MultiChoiceAnswer, HouseholdMemberGroup, Survey, GroupCondition, EnumerationArea
from survey.services.simple_indicator_service import SimpleIndicatorService
from survey.tests.base_test import BaseTest


class MultiChoiceQuestionSimpleIndicatorServiceTest(BaseTest):
    def setUp(self):
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1)
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.region = LocationType.objects.create(name="Region", slug="region")
        self.district = LocationType.objects.create(name="District", slug='district')

        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.west = Location.objects.create(name="WEST", type=self.region, tree_parent=self.uganda)
        self.central = Location.objects.create(name="CENTRAL", type=self.region, tree_parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", tree_parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", tree_parent=self.west, type=self.district)
        self.ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
        self.ea.locations.add(self.kampala)
        self.mbarara_ea = EnumerationArea.objects.create(name="EA3", survey=self.survey)
        self.mbarara_ea.locations.add(self.mbarara)


        backend = Backend.objects.create(name='something')

        self.investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", ea=self.ea,
                                                   backend=backend)
        self.investigator_2 = Investigator.objects.create(name="Investigator 1", mobile_number="33331", ea=self.mbarara_ea,
                                                     backend=backend)

        health_module = QuestionModule.objects.create(name="Health")
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.question_3 = Question.objects.create(text="This is a question",
                                                  answer_type=Question.MULTICHOICE, order=3,
                                                  module=health_module, group=member_group)
        self.yes_option = QuestionOption.objects.create(question=self.question_3, text="Yes", order=1)
        self.no_option = QuestionOption.objects.create(question=self.question_3, text="No", order=2)

        self.question_3.batches.add(self.batch)

        self.indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
                                             batch=self.batch, module=health_module)
        self.formula = Formula.objects.create(count=self.question_3, indicator=self.indicator)

        self.household_head_1 = self.create_household_head(0, self.investigator)
        self.household_head_2 = self.create_household_head(1, self.investigator)
        self.household_head_3 = self.create_household_head(2, self.investigator)
        self.household_head_4 = self.create_household_head(3, self.investigator)
        self.household_head_5 = self.create_household_head(4, self.investigator)

        self.household_head_6 = self.create_household_head(5, self.investigator_2)
        self.household_head_7 = self.create_household_head(6, self.investigator_2)
        self.household_head_8 = self.create_household_head(7, self.investigator_2)
        self.household_head_9 = self.create_household_head(8, self.investigator_2)

    def test_gets_location_names_and_data_series_for_a_parent_location_and_formula(self):
        self.investigator.member_answered(self.question_3, self.household_head_1, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, self.household_head_2, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, self.household_head_3, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, self.household_head_4, self.no_option.order, self.batch)
        self.investigator.member_answered(self.question_3, self.household_head_5, self.no_option.order, self.batch)

        self.investigator_2.member_answered(self.question_3, self.household_head_6, self.yes_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, self.household_head_7, self.yes_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, self.household_head_8, self.no_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, self.household_head_9, self.no_option.order, self.batch)

        simple_indicator_service = SimpleIndicatorService(self.formula, self.uganda)
        region_responses = [{'data': [3, 2], 'name': self.yes_option.text}, {'data': [2, 2], 'name': self.no_option.text}]
        data_series, location = simple_indicator_service.get_location_names_and_data_series()
        self.assertEquals([self.central.name, self.west.name],  location)
        self.assertEquals(region_responses,  data_series)

    def test_formats_details_data(self):
        self.investigator.member_answered(self.question_3, self.household_head_1, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, self.household_head_2, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, self.household_head_3, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, self.household_head_4, self.no_option.order, self.batch)
        self.investigator.member_answered(self.question_3, self.household_head_5, self.no_option.order, self.batch)

        self.investigator_2.member_answered(self.question_3, self.household_head_6, self.yes_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, self.household_head_7, self.yes_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, self.household_head_8, self.no_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, self.household_head_9, self.no_option.order, self.batch)

        kibungo = Location.objects.create(name="Kibungo", type=self.district, tree_parent=self.west)
        mpigi = Location.objects.create(name="Mpigi", type=self.district, tree_parent=self.central)
        table_row_1 = {'Region': self.central.name, 'District': self.kampala.name, self.yes_option.text: 3, self.no_option.text: 2,'Total': 5}
        table_row_2 = {'Region': self.central.name, 'District': mpigi.name, self.yes_option.text: 0, self.no_option.text: 0,'Total': 0}
        table_row_3 = {'Region': self.west.name, 'District': kibungo.name, self.yes_option.text: 0, self.no_option.text: 0,'Total': 0}
        table_row_4 = {'Region': self.west.name, 'District': self.mbarara.name, self.yes_option.text: 2, self.no_option.text: 2,'Total': 4}
        expected_table_data = [table_row_1, table_row_2, table_row_3, table_row_4]

        simple_indicator_service = SimpleIndicatorService(self.formula, self.uganda)
        tabulated_data = simple_indicator_service.tabulated_data_series()

        self.assertEqual(4, len(tabulated_data))
        for i in range(4):
            self.assertEqual(expected_table_data[i], tabulated_data[i])


class GroupCountSimpleIndicatorServiceTest(BaseTest):
    def setUp(self):
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1, survey=self.survey)
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.region = LocationType.objects.create(name="Region", slug="region")
        self.district = LocationType.objects.create(name="District", slug='district')

        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.west = Location.objects.create(name="WEST", type=self.region, tree_parent=self.uganda)
        self.central = Location.objects.create(name="CENTRAL", type=self.region, tree_parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", tree_parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", tree_parent=self.west, type=self.district)
        self.ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
        self.ea.locations.add(self.kampala)
        self.mbarara_ea = EnumerationArea.objects.create(name="EA3", survey=self.survey)
        self.mbarara_ea.locations.add(self.mbarara)

        backend = Backend.objects.create(name='something')

        health_module = QuestionModule.objects.create(name="Health")
        self.investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", ea=self.ea,
                                                        backend=backend)
        self.investigator_2 = Investigator.objects.create(name="Investigator 1", mobile_number="33331",
                                                          ea=self.mbarara_ea,
                                                          backend=backend)

        self.general_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=2)

        general_condition = GroupCondition.objects.create(attribute="GENERAL", value="HEAD", condition='EQUALS')
        self.general_group.conditions.add(general_condition)

        self.household_head_1 = self.create_household_head(0, self.investigator, survey=self.survey)
        self.household_head_2 = self.create_household_head(1, self.investigator, survey=self.survey)
        self.household_head_3 = self.create_household_head(2, self.investigator, survey=self.survey)
        self.household_head_4 = self.create_household_head(3, self.investigator, survey=self.survey)
        self.household_head_5 = self.create_household_head(4, self.investigator, survey=self.survey)

        self.household_head_6 = self.create_household_head(5, self.investigator_2, survey=self.survey)
        self.household_head_7 = self.create_household_head(6, self.investigator_2, survey=self.survey)
        self.household_head_8 = self.create_household_head(7, self.investigator_2, survey=self.survey)
        self.household_head_9 = self.create_household_head(8, self.investigator_2, survey=self.survey)

        self.indicator = Indicator.objects.create(name="indicator name", description="rajni indicator",
                                                  measure='Percentage', batch=self.batch, module=health_module)
        self.formula = Formula.objects.create(groups=self.general_group, indicator=self.indicator)

    def test_gets_location_names_and_data_series_for_a_parent_location_and_formula(self):
        simple_indicator_service = SimpleIndicatorService(self.formula, self.uganda)
        region_responses = [{'data': [5, 4], 'name': self.general_group.name}]
        data_series, location = simple_indicator_service.get_location_names_and_data_series()
        self.assertEquals([self.central.name, self.west.name],  location)
        self.assertEquals(region_responses,  data_series)

    def test_formats_details_data(self):
        kibungo = Location.objects.create(name="Kibungo", type=self.district, tree_parent=self.west)
        mpigi = Location.objects.create(name="Mpigi", type=self.district, tree_parent=self.central)
        table_row_1 = {'Region': self.central.name, 'District': self.kampala.name, self.general_group.name: 5, 'Total': 5}
        table_row_2 = {'Region': self.central.name, 'District': mpigi.name, self.general_group.name: 0, 'Total': 0}
        table_row_3 = {'Region': self.west.name, 'District': kibungo.name, self.general_group.name: 0, 'Total': 0}
        table_row_4 = {'Region': self.west.name, 'District': self.mbarara.name, self.general_group.name: 4, 'Total': 4}
        expected_table_data = [table_row_1, table_row_2, table_row_3, table_row_4]

        simple_indicator_service = SimpleIndicatorService(self.formula, self.uganda)
        tabulated_data = simple_indicator_service.tabulated_data_series()

        self.assertEqual(4, len(tabulated_data))
        for i in range(4):
            self.assertEqual(expected_table_data[i], tabulated_data[i])

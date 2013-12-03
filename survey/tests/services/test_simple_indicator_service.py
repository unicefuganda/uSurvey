from random import randint
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Backend, Investigator, QuestionModule, Question, QuestionOption, Indicator, Formula, Household, HouseholdHead, Batch, MultiChoiceAnswer, HouseholdMemberGroup
from survey.services.simple_indicator_service import SimpleIndicatorService
from survey.tests.base_test import BaseTest


class SimpleIndicatorServiceTest(BaseTest):
    def create_household_head(self, uid, investigator):
        self.household = Household.objects.create(investigator=investigator, location=investigator.location,
                                                  uid=uid)
        return HouseholdHead.objects.create(household=self.household, surname="Name " + str(randint(1, 9999)),
                                            date_of_birth="1990-02-09")

    def setUp(self):
        self.batch = Batch.objects.create(order=1)

    def test_returns_options_counts_given_list_of_locations(self):
        country = LocationType.objects.create(name="Country", slug="country")
        region = LocationType.objects.create(name="Region", slug="region")
        district = LocationType.objects.create(name="District", slug='district')

        uganda = Location.objects.create(name="Uganda", type=country)
        west = Location.objects.create(name="WEST", type=region, tree_parent=uganda)
        central = Location.objects.create(name="CENTRAL", type=region, tree_parent=uganda)
        kampala = Location.objects.create(name="Kampala", tree_parent=central, type=district)
        mbarara = Location.objects.create(name="Mbarara", tree_parent=west, type=district)


        backend = Backend.objects.create(name='something')

        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=kampala,
                                                   backend=backend)
        investigator_2 = Investigator.objects.create(name="Investigator 1", mobile_number="33331", location=mbarara,
                                                     backend=backend)

        health_module = QuestionModule.objects.create(name="Health")
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.question_3 = Question.objects.create(text="This is a question",
                                                  answer_type=Question.MULTICHOICE, order=3,
                                                  module=health_module, group=member_group)
        yes_option = QuestionOption.objects.create(question=self.question_3, text="Yes", order=1)
        no_option = QuestionOption.objects.create(question=self.question_3, text="No", order=2)

        self.question_3.batches.add(self.batch)

        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
                                             batch=self.batch, module=health_module)
        formula = Formula.objects.create(count=self.question_3, indicator=indicator)

        household_head_1 = self.create_household_head(0, investigator)
        household_head_2 = self.create_household_head(1, investigator)
        household_head_3 = self.create_household_head(2, investigator)
        household_head_4 = self.create_household_head(3, investigator)
        household_head_5 = self.create_household_head(4, investigator)

        household_head_6 = self.create_household_head(5, investigator_2)
        household_head_7 = self.create_household_head(6, investigator_2)
        household_head_8 = self.create_household_head(7, investigator_2)
        household_head_9 = self.create_household_head(8, investigator_2)

        investigator.member_answered(self.question_3, household_head_1, yes_option.order, self.batch)
        investigator.member_answered(self.question_3, household_head_2, yes_option.order, self.batch)
        investigator.member_answered(self.question_3, household_head_3, yes_option.order, self.batch)
        investigator.member_answered(self.question_3, household_head_4, no_option.order, self.batch)
        investigator.member_answered(self.question_3, household_head_5, no_option.order, self.batch)

        investigator_2.member_answered(self.question_3, household_head_6, yes_option.order, self.batch)
        investigator_2.member_answered(self.question_3, household_head_7, yes_option.order, self.batch)
        investigator_2.member_answered(self.question_3, household_head_8, no_option.order, self.batch)
        investigator_2.member_answered(self.question_3, household_head_9, no_option.order, self.batch)

        simple_indicator_service = SimpleIndicatorService(formula, uganda)
        region_responses = {central: {yes_option.text: 3, no_option.text: 2},
                            west: {yes_option.text: 2, no_option.text: 2}}
        self.assertEquals(simple_indicator_service.hierarchical_count(), region_responses)

        simple_indicator_service = SimpleIndicatorService(formula, central)
        central_region_responses = {kampala: {yes_option.text: 3, no_option.text: 2}}
        self.assertEquals(simple_indicator_service.hierarchical_count(), central_region_responses)

        simple_indicator_service = SimpleIndicatorService(formula, west)
        west_region_responses = {mbarara: {yes_option.text: 2, no_option.text: 2}}
        self.assertEquals(simple_indicator_service.hierarchical_count(), west_region_responses)
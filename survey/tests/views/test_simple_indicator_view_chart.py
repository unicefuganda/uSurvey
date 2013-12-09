from random import randint
from django.contrib.auth.models import User
from django.test.client import Client
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import HouseholdMemberGroup, GroupCondition, QuestionModule, Indicator, Household, HouseholdHead, LocationTypeDetails, Batch
from survey.models.backend import Backend
from survey.models.investigator import Investigator

from survey.models.formula import *
from survey.models.question import Question, QuestionOption
from survey.tests.base_test import BaseTest


class SimpleIndicatorChartViewTest(BaseTest):
    def create_household_head(self, uid, investigator):
        self.household = Household.objects.create(investigator=investigator, location=investigator.location,
                                                  uid=uid)
        return HouseholdHead.objects.create(household=self.household, surname="Name " + str(randint(1, 9999)),
                                            date_of_birth="1990-02-09")

    def setUp(self):
        self.client = Client()
        self.member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)

        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_aggregates')
        self.client.login(username='Rajni', password='I_Rock')

        self.country = LocationType.objects.create(name='Country', slug='country')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.village = LocationType.objects.create(name='Village', slug='village')

        region = LocationType.objects.create(name="Region", slug="region")
        self.uganda = Location.objects.create(name="Uganda", type=self.country)

        LocationTypeDetails.objects.create(location_type=self.country, country=self.uganda)
        LocationTypeDetails.objects.create(location_type=region, country=self.uganda)
        LocationTypeDetails.objects.create(location_type=self.district, country=self.uganda)
        LocationTypeDetails.objects.create(location_type=self.village, country=self.uganda)

        self.west = Location.objects.create(name="WEST", type=region, tree_parent=self.uganda)
        self.central = Location.objects.create(name="CENTRAL", type=region, tree_parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", tree_parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", tree_parent=self.west, type=self.district)
        self.batch = Batch.objects.create(order=1)
        backend = Backend.objects.create(name='BACKEND')

        self.investigator = Investigator.objects.create(name="Investigator 1", mobile_number="122000", location=self.kampala,
                                                   backend=backend)
        self.investigator_2 = Investigator.objects.create(name="Investigator 1", mobile_number="3333331", location=self.mbarara,
                                                     backend=backend)

        health_module = QuestionModule.objects.create(name="Health")
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=33)
        self.question_3 = Question.objects.create(text="This is a question",
                                                  answer_type=Question.MULTICHOICE, order=3,
                                                  module=health_module, group=member_group)
        self.yes_option = QuestionOption.objects.create(question=self.question_3, text="Yes", order=1)
        self.no_option = QuestionOption.objects.create(question=self.question_3, text="No", order=2)

        self.question_3.batches.add(self.batch)

        self.indicator = Indicator.objects.create(name="ITN 4.5", description="rajni indicator", measure='Percentage',
                                             batch=self.batch, module=health_module)
        self.formula = Formula.objects.create(count=self.question_3, indicator=self.indicator)

    def test_get_data_for_simple_indicator_chart(self):
        household_head_1 = self.create_household_head(0, self.investigator)
        household_head_2 = self.create_household_head(1, self.investigator)
        household_head_3 = self.create_household_head(2, self.investigator)
        household_head_4 = self.create_household_head(3, self.investigator)
        household_head_5 = self.create_household_head(4, self.investigator)

        household_head_6 = self.create_household_head(5, self.investigator_2)
        household_head_7 = self.create_household_head(6, self.investigator_2)
        household_head_8 = self.create_household_head(7, self.investigator_2)
        household_head_9 = self.create_household_head(8, self.investigator_2)

        self.investigator.member_answered(self.question_3, household_head_1, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, household_head_2, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, household_head_3, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, household_head_4, self.no_option.order, self.batch)
        self.investigator.member_answered(self.question_3, household_head_5, self.no_option.order, self.batch)

        self.investigator_2.member_answered(self.question_3, household_head_6, self.yes_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, household_head_7, self.yes_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, household_head_8, self.no_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, household_head_9, self.no_option.order, self.batch)
        url = "/indicators/%s/simple/" % self.indicator.id
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('formula/simple_indicator.html', templates)
        self.assertIsNotNone(response.context['locations'])
        self.assertIsNotNone(response.context['request'])
        self.assertEquals(response.context['location_names'], [self.central.name, self.west.name])
        region_data_series = [{'data': [3, 2], 'name': self.yes_option.text}, {'data': [2, 2], 'name':self.no_option.text}]
        self.assertEquals(response.context['data_series'], region_data_series)
        table_row_1 = {'Region': self.central.name, 'District': self.kampala.name, self.yes_option.text: 3, self.no_option.text: 2,'Total': 5}
        table_row_2 = {'Region': self.west.name, 'District': self.mbarara.name, self.yes_option.text: 2, self.no_option.text: 2,'Total': 4}
        tabulated_data_series = [table_row_1, table_row_2]
        self.assertEquals(response.context['tabulated_data'], tabulated_data_series)

    def test_get_data_for_simple_indicator_chart_for_the_second_hierarchy_level(self):
        kibungo = Location.objects.create(name="Kibungo", type=self.district, tree_parent=self.west)
        mpigi = Location.objects.create(name="Mpigi", type=self.district, tree_parent=self.central)
        household_head_1 = self.create_household_head(0, self.investigator)
        household_head_2 = self.create_household_head(1, self.investigator)
        household_head_3 = self.create_household_head(2, self.investigator)
        household_head_4 = self.create_household_head(3, self.investigator)
        household_head_5 = self.create_household_head(4, self.investigator)

        household_head_6 = self.create_household_head(5, self.investigator_2)
        household_head_7 = self.create_household_head(6, self.investigator_2)
        household_head_8 = self.create_household_head(7, self.investigator_2)
        household_head_9 = self.create_household_head(8, self.investigator_2)

        self.investigator.member_answered(self.question_3, household_head_1, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, household_head_2, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, household_head_3, self.yes_option.order, self.batch)
        self.investigator.member_answered(self.question_3, household_head_4, self.no_option.order, self.batch)
        self.investigator.member_answered(self.question_3, household_head_5, self.no_option.order, self.batch)

        self.investigator_2.member_answered(self.question_3, household_head_6, self.yes_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, household_head_7, self.yes_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, household_head_8, self.no_option.order, self.batch)
        self.investigator_2.member_answered(self.question_3, household_head_9, self.no_option.order, self.batch)

        url = "/indicators/%s/simple/?location=%s" % (self.indicator.id, self.west.id)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(response.context['location_names'], [kibungo.name, self.mbarara.name])

        region_data_series = [{'data': [0, 2], 'name': self.yes_option.text}, {'data': [0, 2], 'name':self.no_option.text}]
        self.assertEquals(response.context['data_series'], region_data_series)

        url = "/indicators/%s/simple/?location=%s" % (self.indicator.id, self.central.id)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(response.context['location_names'], [self.kampala.name, mpigi.name])

        region_data_series = [{'data': [3, 0], 'name': self.yes_option.text}, {'data': [2, 0], 'name':self.no_option.text}]
        self.assertEquals(response.context['data_series'], region_data_series)
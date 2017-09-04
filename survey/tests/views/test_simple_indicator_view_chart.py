from django.contrib.auth.models import User
from django.test.client import Client
from survey.models.locations import *
from survey.models import HouseholdMemberGroup, Survey, GroupCondition, QuestionModule, Indicator, LocationTypeDetails, \
    Batch, EnumerationArea, HouseholdListing, SurveyHouseholdListing
from survey.models.backend import Backend
from survey.models.interviewer import Interviewer

from survey.models.formula import *
from survey.models.questions import Question, QuestionOption
from survey.tests.base_test import BaseTest
from survey.features.simple_indicator_chart_step import create_household_head


class SimpleIndicatorChartViewTest(BaseTest):

    def setUp(self):
        self.survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        self.client = Client()
        self.member_group = HouseholdMemberGroup.objects.create(
            name="Greater than 2 years", order=1)
        self.condition = GroupCondition.objects.create(
            attribute="AGE", value=2, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)

        User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user(
            'Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_aggregates')
        self.assign_permission_to(raj, 'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')

        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.district = LocationType.objects.create(
            name='District', parent=self.country, slug='district')
        self.village = LocationType.objects.create(
            name='Village', parent=self.district, slug='village')

        self.uganda = Location.objects.create(name="Uganda", type=self.country)

        LocationTypeDetails.objects.create(
            location_type=self.country, country=self.uganda)
        LocationTypeDetails.objects.create(
            location_type=self.district, country=self.uganda)
        LocationTypeDetails.objects.create(
            location_type=self.village, country=self.uganda)

        self.west = Location.objects.create(
            name="WEST", type=self.district, parent=self.uganda)
        self.central = Location.objects.create(
            name="CENTRAL", type=self.district, parent=self.uganda)
        self.kampala = Location.objects.create(
            name="Kampala", parent=self.central, type=self.village)
        self.mbarara = Location.objects.create(
            name="Mbarara", parent=self.west, type=self.village)
        self.batch = Batch.objects.create(order=1)
        backend = Backend.objects.create(name='BACKEND')

        self.ea = EnumerationArea.objects.create(name="EA2")
        self.ea.locations.add(self.kampala)

        mbarara_ea = EnumerationArea.objects.create(name="EA3")
        mbarara_ea.locations.add(self.mbarara)

        self.investigator = Interviewer.objects.create(name="Investigator",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0)
        self.investigator_2 = Interviewer.objects.create(name="Investigator1",
                                                         ea=self.ea,
                                                         gender='1', level_of_education='Primary',
                                                         language='Eglish', weights=0)

        self.health_module = QuestionModule.objects.create(name="Health")
        member_group = HouseholdMemberGroup.objects.create(
            name="Greater than 2 years", order=33)
        self.question_3 = Question.objects.create(identifier='1.1', text="This is a question1", answer_type='Numerical Answer',
                                                  group=self.member_group, batch=self.batch, module=self.health_module)
        self.yes_option = QuestionOption.objects.create(
            question=self.question_3, text="Yes", order=1)
        self.no_option = QuestionOption.objects.create(
            question=self.question_3, text="No", order=2)

        self.indicator = Indicator.objects.create(name="ITN 4.5", description="rajni indicator", measure='Percentage',
                                                  batch=self.batch, module=self.health_module)
        self.formula = Formula.objects.create(
            count=self.question_3, indicator=self.indicator)

    def test_get_data_for_simple_indicator_chart(self):
        household_listing = HouseholdListing.objects.create(
            ea=self.ea, list_registrar=self.investigator, initial_survey=self.survey)
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=self.survey)
        household_head_1 = create_household_head(
            0, self.investigator, household_listing, survey_householdlisting)
        household_head_2 = create_household_head(
            1, self.investigator, household_listing, survey_householdlisting)
        household_head_3 = create_household_head(
            2, self.investigator, household_listing, survey_householdlisting)
        household_head_4 = create_household_head(
            3, self.investigator, household_listing, survey_householdlisting)
        household_head_5 = create_household_head(
            4, self.investigator, household_listing, survey_householdlisting)

        household_head_6 = create_household_head(
            5, self.investigator_2, household_listing, survey_householdlisting)
        household_head_7 = create_household_head(
            6, self.investigator_2, household_listing, survey_householdlisting)
        household_head_8 = create_household_head(
            7, self.investigator_2, household_listing, survey_householdlisting)
        household_head_9 = create_household_head(
            8, self.investigator_2, household_listing, survey_householdlisting)
        url = "/indicators/%s/simple/" % self.indicator.id
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('formula/simple_indicator.html', templates)

        self.assertIsNotNone(response.context['locations_filter'])
        self.assertIsNotNone(response.context['request'])
        self.assertEquals(response.context['location_names'], [
                          self.central.name, self.west.name])
        region_data_series = [{'data': [0, 0], 'name': 'Yes'}, {
            'data': [0, 0], 'name': 'No'}]
        self.assertEquals(response.context['data_series'], region_data_series)

    def test_get_data_for_simple_indicator_chart_for_the_second_hierarchy_level(self):
        kibungo = Location.objects.create(
            name="Kibungo", type=self.district, tree_parent=self.west)
        mpigi = Location.objects.create(
            name="Mpigi", type=self.district, tree_parent=self.central)
        household_listing = HouseholdListing.objects.create(
            ea=self.ea, list_registrar=self.investigator, initial_survey=self.survey)
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=self.survey)
        household_head_1 = create_household_head(0, self.investigator, household_listing, survey_householdlisting)
        household_head_2 = create_household_head(1, self.investigator, household_listing, survey_householdlisting)
        household_head_3 = create_household_head(
            2, self.investigator, household_listing, survey_householdlisting)
        household_head_4 = create_household_head(
            3, self.investigator, household_listing, survey_householdlisting)
        household_head_5 = create_household_head(
            4, self.investigator, household_listing, survey_householdlisting)

        household_head_6 = create_household_head(
            5, self.investigator_2, household_listing, survey_householdlisting)
        household_head_7 = create_household_head(
            6, self.investigator_2, household_listing, survey_householdlisting)
        household_head_8 = create_household_head(
            7, self.investigator_2, household_listing, survey_householdlisting)
        household_head_9 = create_household_head(
            8, self.investigator_2, household_listing, survey_householdlisting)

        url = "/indicators/%s/simple/?location=%s" % (
            self.indicator.id, self.west.id)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(response.context['location_names'], [
                          'CENTRAL', 'WEST'])

        region_data_series = [{'data': [0, 0], 'name': 'Yes'}, {
            'data': [0, 0], 'name': 'No'}]
        self.assertEquals(response.context['data_series'], region_data_series)

        url = "/indicators/%s/simple/?location=%s" % (
            self.indicator.id, self.central.id)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(response.context['location_names'], [
                          'CENTRAL', 'WEST'])

        region_data_series = [{'data': [0, 0], 'name': self.yes_option.text}, {
            'data': [0, 0], 'name':self.no_option.text}]
        self.assertEquals(response.context['data_series'], region_data_series)

    def test_returns_error_message_if_no_formula_is_found_for_that_indicator(self):
        indicator = Indicator.objects.create(name="ITN 4.5", description="rajni indicator", measure='Percentage',
                                             batch=self.batch, module=self.health_module)
        url = "/indicators/%s/simple/?location=%s" % (
            indicator.id, self.west.id)
        response = self.client.get(url)
        message = "No formula was found in this indicator"
        self.assertIn(message, response.cookies['messages'].value)
        self.assertRedirects(response, expected_url='/indicators/')

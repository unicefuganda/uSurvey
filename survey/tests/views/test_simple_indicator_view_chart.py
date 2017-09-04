from django.contrib.auth.models import User
from django.test.client import Client
from survey.models.locations import *
from survey.models import Survey, QuestionModule, Indicator, LocationType, \
    Batch, EnumerationArea
from survey.models.backend import Backend
from survey.models.interviewer import Interviewer

# from survey.models.formula import *
from survey.models.questions import Question, QuestionOption, QuestionSet, ResponseValidation
from survey.tests.base_test import BaseTest
# from survey.features.simple_indicator_chart_step import create_household_head


class SimpleIndicatorChartViewTest(BaseTest):

    def setUp(self):
        self.survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        self.client = Client()

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

        LocationType.objects.create(
            location_type=self.country, country=self.uganda)
        LocationType.objects.create(
            location_type=self.district, country=self.uganda)
        LocationType.objects.create(
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
        # member_group = HouseholdMemberGroup.objects.create(
        #     name="Greater than 2 years", order=33)
        self.survey = Survey.objects.create(name='survey name', description='survey descrpition',
                                            sample_size=10)
        self.qset = QuestionSet.objects.create(name="Females")
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest",
                                                     constraint_message="message")
        self.question_3 = Question.objects.create(identifier='123.1', text="This is a question123.1",
                                                  answer_type='Numerical Answer',
                                                  qset_id=self.qset, batch=self.batch, module=self.question_mod,
                                                  response_validation_id=self.rsp)
        self.yes_option = QuestionOption.objects.create(
            question=self.question_3, text="Yes", order=1)
        self.no_option = QuestionOption.objects.create(
            question=self.question_3, text="No", order=2)

        # self.indicator = Indicator.objects.create(name="ITN 4.5", description="rajni indicator", measure='Percentage',
        #                                           batch=self.batch, module=self.health_module)
        self.indicator = Indicator.objects.create(name='Test Indicator', description="dummy",display_on_dashboard=True,
                                                  formulae="formulae",
                                                  question_set_id=self.qset.id, survey_id=self.survey.id)

    def test_returns_error_message_if_no_formula_is_found_for_that_indicator(self):
        self.survey = Survey.objects.create(name='survey name', description='survey descrpition',
                                            sample_size=10)
        self.qset = QuestionSet.objects.create(name="Females")
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest", constraint_message="message")
        self.batch = Batch.objects.create(
            order=1, name="Batch A", survey=self.survey)
        self.module = QuestionModule.objects.create(
            name='Education', description='Educational Module')
        indicator = Indicator.objects.create(name='Test Indicator', description="dummy",display_on_dashboard=True,
                                             formulae="formulae", question_set_id=self.qset.id,
                                             survey_id=self.survey.id)

        url = "/indicators/%s/simple/?location=%s" % (
            indicator.id, self.west.id)
        response = self.client.get(url)
        message = "No formula was found in this indicator"
        self.assertIn(message, response.cookies['messages'].value)
        self.assertRedirects(response, expected_url='/indicators/')
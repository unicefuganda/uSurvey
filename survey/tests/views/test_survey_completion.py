import datetime
import json
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.test import Client
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Survey, Batch, Investigator, Household, Question, HouseholdMemberGroup, BatchQuestionOrder, HouseholdMemberBatchCompletion, Backend, LocationTypeDetails, EnumerationArea
from survey.models.households import HouseholdMember
from survey.services.completion_rates_calculator import BatchLocationCompletionRates
from survey.tests.base_test import BaseTest
from survey.views.survey_completion import is_valid


class TestSurveyCompletion(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_aggregates')
        self.client.login(username='Rajni', password='I_Rock')
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.region = LocationType.objects.create(name='Region', slug='region')
        self.city = LocationType.objects.create(name='City', slug='city')
        self.parish = LocationType.objects.create(name='Parish', slug='parish')
        self.survey = Survey.objects.create(name='Survey 1')

        self.africa = Location.objects.create(name='Africa', type=self.country)
        LocationTypeDetails.objects.create(country=self.africa, location_type=self.country)
        LocationTypeDetails.objects.create(country=self.africa, location_type=self.region)
        LocationTypeDetails.objects.create(country=self.africa, location_type=self.city)
        LocationTypeDetails.objects.create(country=self.africa, location_type=self.parish)

        self.uganda = Location.objects.create(name='Uganda', type=self.region, tree_parent=self.africa)
        self.abim = Location.objects.create(name='Abim', tree_parent=self.uganda, type=self.city)
        self.kampala = Location.objects.create(name='Kampala', tree_parent=self.uganda, type=self.city)
        self.bukoto = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.parish)
        self.kampala_ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
        self.kampala_ea.locations.add(self.kampala)
        self.abim_ea = EnumerationArea.objects.create(name="ABIM EA", survey=self.survey)
        self.abim_ea.locations.add(self.abim)

        self.city_ea = EnumerationArea.objects.create(name="CITY EA", survey=self.survey)
        self.city_ea.locations.add(self.bukoto)

        self.investigator_1 = Investigator.objects.create(name='some_inv', mobile_number='123456789', male=True,
                                                          ea=self.kampala_ea)
        self.investigator_2 = Investigator.objects.create(name='some_inv', mobile_number='123456788', male=True,
                                                          ea=self.city_ea)

        self.household_1 = Household.objects.create(investigator=self.investigator_1, ea=self.kampala_ea,
                                                    survey=self.survey)
        self.household_2 = Household.objects.create(investigator=self.investigator_2, ea=self.city_ea,
                                                    survey=self.survey)
        self.member_1 = HouseholdMember.objects.create(household=self.household_1,
                                                       date_of_birth=datetime.date(1980, 05, 01))
        self.member_2 = HouseholdMember.objects.create(household=self.household_2,
                                                       date_of_birth=datetime.date(1980, 05, 3))

        self.batch = Batch.objects.create(order=1, name='somebatch', survey=self.survey)

    def test_should_render_success_status_code_on_GET(self):
        response = self.client.get('/surveys/completion/')
        self.assertEqual(response.status_code, 200)

    def test_should_render_template(self):
        response = self.client.get('/surveys/completion/')
        templates = [template.name for template in response.templates]
        self.assertIn('aggregates/completion_status.html', templates)

    def test_should_render_context_data(self):
        survey = Survey.objects.create()
        batch = Batch.objects.create()
        response = self.client.get('/surveys/completion/')
        self.assertIn('survey_completion_rates', response.context['action'])
        locations = response.context['locations'].get_widget_data()
        self.assertEquals(len(locations.keys()), 2)
        self.assertEquals(locations.keys()[0], 'region')
        self.assertEquals(len(locations['region']), 1)
        self.assertEquals(locations['region'][0], self.uganda)
        self.assertEquals(locations.keys()[1], 'city')
        self.assertEquals(len(locations['city']), 0)

    def test_validates_when_location_is_present_in_parameters_and_parameters_contains_batch_key(self):
        self.assertTrue(is_valid({'location': '', 'batch': '1'}))
        self.assertTrue(is_valid({'location': '2', 'batch': '1', 'ea': '1'}))
        self.assertTrue(is_valid({'location': '2', 'batch': '1', 'ea': ''}))

    def test_show_retrieves_high_level_completion_rates_if_no_location_is_provided(self):
        data = {'location': '',
                'batch': str(self.batch.pk),
                'survey': self.survey.id,
                'ea': ''}
        response = self.client.post('/surveys/completion/', data=data)
        self.assertIn(self.uganda, response.context['completion_rates'].locations)
        self.assertIsNotNone(response.context['request'])

    def test_knows_to_retrieve_completion_for_locations_that_have_no_tree_parent_if_country_type_does_not_exist(self):
        LocationType.objects.filter(name__iexact='country').delete()

        location_with_no_parent = Location.objects.create(name='Abim', type=self.city)
        another_location_with_no_parent = Location.objects.create(name='Kampala', type=self.city)
        form_data = {'survey': self.batch.survey.id, 'location': '', 'batch': str(self.batch.pk), 'ea': ''}
        response = self.client.post('/surveys/completion/', data=form_data)
        self.assertIn(location_with_no_parent, response.context['completion_rates'].locations)
        self.assertIn(another_location_with_no_parent, response.context['completion_rates'].locations)
        self.assertIsNotNone(response.context['request'])

    def test_should_validate_params(self):
        self.assertFalse(is_valid({'location': '2', 'batch': 'NOT_A_DIGIT'}))
        self.assertFalse(is_valid({'location': '2', 'batch': ''}))
        self.assertFalse(is_valid({'location': '2', 'batch': '2', 'ea': 'NOT_A_DIGIT'}))

    def test_should_render_location_children_if_location_is_posted(self):
        data = {'location': str(self.uganda.pk),
                'batch': str(self.batch.pk),
                'survey': self.survey.id,
                'ea': ''}
        response = self.client.post('/surveys/completion/', data=data)
        self.assertEqual(2, len(response.context['completion_rates'].attributes()))
        index_of_abim = 0
        index_of_kampala = 1

        self.assertEqual(self.abim, response.context['completion_rates'].attributes()[index_of_abim]['location'])
        self.assertEqual(self.kampala, response.context['completion_rates'].attributes()[index_of_kampala]['location'])

    def test_should_render_total_number_of_household_under_child_locations(self):
        data = {'location': str(self.uganda.pk),
                'batch': str(self.batch.pk),
                'survey': self.survey.id,
                'ea': ''}
        response = self.client.post('/surveys/completion/', data=data)
        self.assertEqual(2, len(response.context['completion_rates'].attributes()))
        index_of_abim = 0
        index_of_kampala = 1

        self.assertEqual(0, response.context['completion_rates'].attributes()[index_of_abim]['total_households'])
        self.assertEqual(2, response.context['completion_rates'].attributes()[index_of_kampala]['total_households'])

    def test_should_render_household_completion_percentage_in_child_locations(self):
        self.batch.completed_households.create(householdmember=self.member_1)
        data = {'survey': self.survey.id,
                'location': str(self.uganda.pk),
                'batch': str(self.batch.pk),
                'ea': ''}
        response = self.client.post('/surveys/completion/', data=data)
        rates_attributes = response.context['completion_rates'].attributes()
        self.assertEqual(2, len(rates_attributes))
        index_of_abim = 0
        index_of_kampala = 1
        self.assertEqual(0, rates_attributes[index_of_abim]['completed_households_percent'])
        self.assertEqual(50, rates_attributes[index_of_kampala]['completed_households_percent'])

    def test_should_return_household_objects_if_lowest_level_selected(self):
        data = {'location': str(self.bukoto.pk),
                'batch': str(self.batch.pk),
                'survey': self.survey.id,
                'ea': self.city_ea.id}

        response = self.client.post('/surveys/completion/', data=data)
        self.assertEqual(1, len(response.context['completion_rates'].interviewed_households()))
        self.assertEqual(self.household_2,
                         response.context['completion_rates'].interviewed_households()[0]['household'])

    def test_should_render_context_if_lowest_level_selected(self):
        form_data = {'location': str(self.bukoto.pk), 'batch': str(self.batch.pk), 'ea': self.kampala_ea.id,
                     'survey': self.survey.id}
        response = self.client.post('/surveys/completion/', data=form_data)
        self.assertEqual(self.kampala_ea, response.context['selected_ea'])
        self.assertEqual(self.investigator_1, response.context['investigator'])
        self.assertIsInstance(response.context['completion_rates'], BatchLocationCompletionRates)
        self.assertEqual(0, response.context['completion_rates'].percent_completed_households())

        self.batch.completed_households.create(householdmember=self.member_1)

        response = self.client.post('/surveys/completion/', data=form_data)
        self.assertEqual(100, response.context['completion_rates'].percent_completed_households())

    def test_should_render_interviewed_number_of_members_if_lowest_level_selected(self):
        member_group = HouseholdMemberGroup.objects.create(name='group1', order=1)
        question = Question.objects.create(text="some question", answer_type=Question.NUMBER, order=1,
                                           group=member_group)
        self.batch.questions.add(question)
        BatchQuestionOrder.objects.create(question=question, batch=self.batch, order=1)
        member_1 = HouseholdMember.objects.create(household=self.household_2,
                                                  date_of_birth=datetime.datetime(2000, 02, 02))
        member_2 = HouseholdMember.objects.create(household=self.household_2,
                                                  date_of_birth=datetime.datetime(2000, 02, 02))
        self.investigator_2.member_answered(question, member_1, 1, self.batch)
        data = {'survey': self.survey.id,
                'location': str(self.uganda.pk),
                'batch': str(self.batch.pk),
                'ea': self.city_ea.id}
        response = self.client.post('/surveys/completion/', data=data)

        self.assertEqual(1, len(response.context['completion_rates'].interviewed_households()))
        self.assertEqual(self.household_2,
                         response.context['completion_rates'].interviewed_households()[0]['household'])
        self.assertEqual(1, response.context['completion_rates'].interviewed_households()[0][
            'number_of_member_interviewed'])

    def test_restricted_permissions(self):
        self.assert_login_required('/surveys/completion/')
        self.assert_restricted_permission_for('/surveys/completion/')

    def test_should_return_date_of_completion_of_household_if_lowest_level_selected(self):
        member_group = HouseholdMemberGroup.objects.create(name='group1', order=1)
        question = Question.objects.create(text="some question", answer_type=Question.NUMBER, order=1,
                                           group=member_group)
        self.batch.questions.add(question)
        BatchQuestionOrder.objects.create(question=question, batch=self.batch, order=1)
        member_1 = HouseholdMember.objects.create(household=self.household_2,
                                                  date_of_birth=datetime.datetime(2000, 02, 02))
        member_2 = HouseholdMember.objects.create(household=self.household_2,
                                                  date_of_birth=datetime.datetime(2000, 02, 02))
        self.investigator_2.member_answered(question, self.member_2, 1, self.batch)
        self.investigator_2.member_answered(question, member_1, 1, self.batch)
        self.investigator_2.member_answered(question, member_2, 1, self.batch)
        data = {'location': str(self.bukoto.pk),
                'batch': str(self.batch.pk),
                'survey': self.survey.id,
                'ea': self.city_ea.id}

        response = self.client.post('/surveys/completion/', data=data)
        expected = HouseholdMemberBatchCompletion.objects.filter(household=self.household_2).latest(
            'created').created.strftime('%d-%b-%Y %H:%M:%S')
        self.assertEqual(1, len(response.context['completion_rates'].interviewed_households()))
        self.assertEqual(self.household_2, response.context['completion_rates'].interviewed_households()[0]['household'])
        self.assertEqual(expected, response.context['completion_rates'].interviewed_households()[0]['date_interviewed'])


class HouseholdCompletionJsonViewTest(BaseTest):
    def setUp(self):
        User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_aggregates')
        self.client.login(username='Rajni', password='I_Rock')

        self.survey = Survey.objects.create(name='SurveyA')
        self.country = LocationType.objects.create(name="Country", slug=slugify("country"))
        self.district = LocationType.objects.create(name="District", slug=slugify("district"))
        self.city = LocationType.objects.create(name="City", slug=slugify("city"))
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.abim = Location.objects.create(name="Abim", type=self.district, tree_parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", type=self.city, tree_parent=self.abim)

        self.zombo = Location.objects.create(name="Zombo", type=self.district, tree_parent=self.uganda)
        self.apachi = Location.objects.create(name="Apachi", type=self.city, tree_parent=self.zombo)
        self.apachi_ea = EnumerationArea.objects.create(name="Apachi EA", survey=self.survey)
        self.apachi_ea.locations.add(self.apachi)

        kampala_ea = EnumerationArea.objects.create(name="Kampala EA", survey=self.survey)
        kampala_ea.locations.add(self.kampala)

        self.backend = Backend.objects.create(name='something')
        self.batch = Batch.objects.create(order=1, name='somebatch', survey=self.survey)
        self.batch_2 = Batch.objects.create(order=2, name='somebatch 2', survey=self.survey)

        self.batch.open_for_location(self.abim)
        self.batch.open_for_location(self.zombo)

        self.batch_2.open_for_location(self.abim)
        self.batch_2.open_for_location(self.zombo)

        self.investigator_1 = Investigator.objects.create(name="investigator name_1", mobile_number="9876543210",
                                                          ea=kampala_ea, backend=self.backend)

        self.investigator_2 = Investigator.objects.create(name="investigator name_2", mobile_number="9876543330",
                                                          ea=self.apachi_ea, backend=self.backend)
        self.household_1 = Household.objects.create(investigator=self.investigator_1, ea=kampala_ea,
                                                    survey=self.survey)
        self.household_2 = Household.objects.create(investigator=self.investigator_1, ea=kampala_ea,
                                                    survey=self.survey)
        self.household_3 = Household.objects.create(investigator=self.investigator_1, ea=kampala_ea,
                                                    survey=self.survey)
        self.household_4 = Household.objects.create(investigator=self.investigator_1, ea=kampala_ea,
                                                    survey=self.survey)

    def test_knows_completion_rates_for_location_type(self):
        household_1_member = HouseholdMember.objects.create(household=self.household_1,
                                                            date_of_birth=datetime.date(1980, 05, 01))
        household_2_member = HouseholdMember.objects.create(household=self.household_2,
                                                            date_of_birth=datetime.date(1980, 05, 01))
        household_3_member = HouseholdMember.objects.create(household=self.household_3,
                                                            date_of_birth=datetime.date(1980, 05, 01))
        household_4_member = HouseholdMember.objects.create(household=self.household_4,
                                                            date_of_birth=datetime.date(1980, 05, 01))

        HouseholdMemberBatchCompletion.objects.create(household=self.household_1, householdmember=household_1_member,
                                                      batch=self.batch,
                                                      investigator=self.investigator_1)

        HouseholdMemberBatchCompletion.objects.create(household=self.household_2, householdmember=household_2_member,
                                                      batch=self.batch,
                                                      investigator=self.investigator_1)

        HouseholdMemberBatchCompletion.objects.create(household=self.household_3, householdmember=household_3_member,
                                                      batch=self.batch,
                                                      investigator=self.investigator_1)

        HouseholdMemberBatchCompletion.objects.create(household=self.household_4, householdmember=household_4_member,
                                                      batch=self.batch,
                                                      investigator=self.investigator_1)

        self.household_5 = Household.objects.create(investigator=self.investigator_2, ea=self.apachi_ea,
                                                    survey=self.survey)
        self.household_6 = Household.objects.create(investigator=self.investigator_2, ea=self.apachi_ea,
                                                    survey=self.survey)
        self.household_7 = Household.objects.create(investigator=self.investigator_2, ea=self.apachi_ea,
                                                    survey=self.survey)
        self.household_8 = Household.objects.create(investigator=self.investigator_2, ea=self.apachi_ea,
                                                    survey=self.survey)

        household_5_member = HouseholdMember.objects.create(household=self.household_5,
                                                            date_of_birth=datetime.date(1980, 05, 01))
        household_6_member = HouseholdMember.objects.create(household=self.household_6,
                                                            date_of_birth=datetime.date(1980, 05, 01))

        HouseholdMember.objects.create(household=self.household_7, date_of_birth=datetime.date(1980, 05, 01))
        HouseholdMember.objects.create(household=self.household_8, date_of_birth=datetime.date(1980, 05, 01))

        HouseholdMemberBatchCompletion.objects.create(household=self.household_5, householdmember=household_5_member,
                                                      batch=self.batch, investigator=self.investigator_2)
        HouseholdMemberBatchCompletion.objects.create(household=self.household_6, householdmember=household_6_member,
                                                      batch=self.batch, investigator=self.investigator_2)
        response = self.client.get('/survey/%s/completion/json/' % self.survey.pk)
        self.assertEqual(response.status_code, 200)
        completion_rates = json.loads(response.content)
        self.assertEqual(completion_rates[self.zombo.name], 25.0)
        self.assertEqual(completion_rates[self.abim.name], 50.0)
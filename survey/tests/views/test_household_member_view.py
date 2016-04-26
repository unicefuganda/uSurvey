from datetime import date
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test.client import Client
from survey.models.locations import Location,LocationType
from survey.forms.householdMember import HouseholdMemberForm
from survey.models.households import HouseholdMember, HouseholdHead, Household, HouseholdListing, SurveyHouseholdListing
from survey.models.backend import Backend
from survey.models.interviewer import Interviewer
from survey.tests.base_test import BaseTest
from survey.models import EnumerationArea, Survey

class HouseholdMemberViewsTest(BaseTest):
    def setUp(self):
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_households', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        self.client = Client()
        self.client.login(username='Rajni', password='I_Rock')

        country = LocationType.objects.create(name="Country", slug="country")

        uganda = Location.objects.create(name="Uganda", type=country)
        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(uganda)
        self.investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        survey = Survey.objects.create(name="Survey A", description="open survey", has_sampling=True)
        self.household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=self.investigator,initial_survey=survey)
        self.household = Household.objects.create(house_number=123456,listing=self.household_listing,physical_address='Test address',
                                             last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",
                                             head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=self.household_listing,survey=survey)
        HouseholdHead.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth=date(1988,01,01) ,
                                                          household=self.household,survey_listing=survey_householdlisting,
                                                          registrar=self.investigator,registration_channel="ODK Access",occupation="Agricultural labor",level_of_education="Primary",
                                                      resident_since=date(1989,02,02))
        self.household_member = HouseholdMember.objects.create(surname="sur123", first_name='fir123', gender='MALE', date_of_birth=date(1988,01,01),
                                                          household=self.household,survey_listing=survey_householdlisting,
                                                          registrar=self.investigator,registration_channel="ODK Access")

    def test_new_should_have_household_member_form_in_response_context_for_get(self):
        response = self.client.post('/households/%d/member/new/' % int(self.household.id))

        self.assertEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('household_member/new.html', templates)

        self.assertIsInstance(response.context['member_form'], HouseholdMemberForm)
        self.assertEqual(response.context['button_label'], 'Create')

    def test_should_have_member_form_in_context(self):
        response = self.client.get(
            '/households/%d/member/%d/edit/' % (int(self.household.id), int(self.household_member.id)))
        self.assertEqual(response.status_code, 200)

        templates = [template.name for template in response.templates]
        self.assertIn('household_member/new.html', templates)

        self.assertIsInstance(response.context['member_form'], HouseholdMemberForm)
        self.assertEqual(response.context['button_label'], 'Save')

    def test_should_have_the_member_information_as_values_on_the_form(self):
        response = self.client.get(
            '/households/%d/member/%d/edit/' % (int(self.household.id), int(self.household_member.id)))

        member_form = response.context['member_form']

        self.assertEqual(member_form.instance.surname, self.household_member.surname)
        self.assertEqual(member_form.instance.date_of_birth, self.household_member.date_of_birth)
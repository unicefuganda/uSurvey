from datetime import date, datetime
from django.test.client import Client
from lettuce.django import django_url
from rapidsms.contrib.locations.models import Location
from survey.forms.householdMember import HouseholdMemberForm
from survey.models import Investigator, Backend, Household, HouseholdMember
from django.contrib.auth.models import User
from survey.tests.base_test import BaseTest


class HouseholdMemberViewsTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_households')
        self.client.login(username='Rajni', password='I_Rock')
        
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))
        self.household = Household.objects.create(investigator=investigator)
        self.household_member = HouseholdMember.objects.create(name='member1', date_of_birth=(date(2013, 8, 30)),
                                                               male=True,
                                                               household=self.household)

    def test_new_should_have_household_member_form_in_response_context_for_get(self):
        response = self.client.get('/households/%d/member/new/' % int(self.household.id))

        self.assertEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('household_member/new.html', templates)

        self.assertIsInstance(response.context['member_form'], HouseholdMemberForm)
        self.assertEqual(response.context['button_label'], 'Create')

    def test_new_should_redirect_on_post(self):
        form_data = {'name': 'xyz',
                     'date_of_birth': date(1980, 05, 01),
                     'male': True
        }

        response = self.client.post('/households/%d/member/new/' % int(self.household.id), data=form_data)

        self.assertEqual(response.status_code, 302)

    def test_new_should_create_new_member_on_post_who_belongs_to_household_selected(self):
        form_data = {'name': 'xyz',
                     'date_of_birth': date(1980, 05, 01),
                     'male': True
        }

        response = self.client.post('/households/%d/member/new/' % int(self.household.id), data=form_data)
        self.assertEqual((HouseholdMember.objects.all()).count(), 2)
        success_message = 'Household member successfully created.'
        household_member = HouseholdMember.objects.get(name=form_data['name'])
        self.failUnless(household_member)
        self.assertEqual(household_member.household, self.household)
        self.assertTrue(success_message in response.cookies['messages'].value)

    def test_should_throw_error_if_a_member_is_being_created_for_does_not_exist_and_redirect_to_households_for_get(
            self):
        response = self.client.get('/households/%d/member/new/' % (int(self.household.id) + 1))

        error_message = "There are  no households currently registered  for this ID."

        self.assertEqual(response.status_code, 302)
        self.assertTrue(error_message in response.cookies['messages'].value)

    def test_should_show_error_if_being_created_for_household_that_does_not_exist_and_redirect_to_households_for_post(
            self):
        form_data = {'name': 'xyz',
                     'date_of_birth': date(1980, 05, 01),
                     'male': True
        }

        response = self.client.post('/households/%d/member/new/' % (int(self.household.id) + 1), data=form_data)

        error_message = "There are  no households currently registered  for this ID."

        self.assertEqual(response.status_code, 302)
        self.assertTrue(error_message in response.cookies['messages'].value)

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

        self.assertEqual(member_form.instance.name, self.household_member.name)
        self.assertEqual(member_form.instance.date_of_birth, self.household_member.date_of_birth)
        self.assertTrue(member_form.instance.male)

    def test_should_update_member_information_on_post(self):
        form_data = {'name': 'new_name',
                     'date_of_birth': date(1981, 06, 01),
                     'male': False
        }
        response = self.client.post(
            '/households/%d/member/%d/edit/' % (int(self.household.id), int(self.household_member.id)), data=form_data)

        member = HouseholdMember.objects.filter(name=self.household_member.name)
        self.failIf(member)

        updated_member = HouseholdMember.objects.get(id=self.household_member.id)
        self.assertEqual(updated_member.name,form_data['name'])
        self.assertEqual(updated_member.date_of_birth,form_data['date_of_birth'])
        self.assertFalse(updated_member.male)
        self.assertEqual(response.status_code, 302)

    def test_should_show_successfully_edited_on_post_if_valid_information(self):
        form_data = {'name': 'new_name',
                     'date_of_birth': date(1981, 06, 01),
                     'male': False
        }

        response = self.client.post(
            '/households/%d/member/%d/edit/' % (int(self.household.id), int(self.household_member.id)), data=form_data)

        success_message = "Household member successfully edited."

        self.assertTrue(success_message in response.cookies['messages'].value)

    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/households/%d/member/new/' % int(self.household.id))
        self.assert_restricted_permission_for('/households/%d/member/%d/edit/' % (int(self.household.id), int(self.household_member.id)))        

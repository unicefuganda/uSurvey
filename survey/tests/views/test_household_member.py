from datetime import date, datetime
from django.test.client import Client
from django.test.testcases import TestCase
from lettuce.django import django_url
from rapidsms.contrib.locations.models import Location
from survey.forms.householdMember import HouseholdMemberForm
from survey.models import Investigator, Backend, Household, HouseholdMember


class HouseholdMemberViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        uganda = Location.objects.create(name="Uganda")
        investigator = Investigator.objects.create(name="inv1", location=uganda,
                                                   backend=Backend.objects.create(name='something'))
        self.household = Household.objects.create(investigator=investigator)

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
        self.assertEqual((HouseholdMember.objects.all()).count(), 1)
        success_message = 'Household member successfully created.'
        household_member = HouseholdMember.objects.get(name=form_data['name'])
        self.failUnless(household_member)
        self.assertEqual(household_member.household, self.household)
        self.assertTrue(success_message in response.cookies['messages'].value)

    def test_should_throw_error_if_a_member_is_being_created_for_does_not_exist_and_redirect_to_households_for_get(self):
        response = self.client.get('/households/%d/member/new/' % (int(self.household.id) + 1))

        error_message = "There are  no households currently registered  for this ID."

        self.assertEqual(response.status_code, 302)
        self.assertTrue(error_message in response.cookies['messages'].value)

    def test_should_throw_error_if_a_member_is_being_created_for_does_not_exist_and_redirect_to_households_for_post(self):
        form_data = {'name': 'xyz',
                     'date_of_birth': date(1980, 05, 01),
                     'male': True
        }

        response = self.client.post('/households/%d/member/new/' % (int(self.household.id) + 1), data=form_data)

        error_message = "There are  no households currently registered  for this ID."

        self.assertEqual(response.status_code, 302)
        self.assertTrue(error_message in response.cookies['messages'].value)

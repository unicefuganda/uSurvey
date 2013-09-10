from django.test import TestCase
from survey.forms.household import *
from survey.models.households import Household
from survey.models.backend import Backend
from survey.models.investigator import Investigator


class HouseholdFormTest(TestCase):

    def test_valid(self):
        form_data = {'uid': '6'}

        household_form = HouseholdForm(form_data)
        self.assertTrue(household_form.is_valid())
        investigator = Investigator.objects.create(name="test", backend = Backend.objects.create(name='something'))
        household_form.instance.investigator = investigator
        household = household_form.save()
        self.failUnless(household.id)
        household_retrieved = Household.objects.get(investigator=investigator)
        self.assertEqual(household_retrieved, household)

    def test_positive_numbers(self):
        form_data = {
                        'uid': -6,
                    }
        household_form = HouseholdForm(form_data)
        self.assertFalse(household_form.is_valid())
        message = "Ensure this value is greater than or equal to 0."
        self.assertEquals(household_form.errors['uid'], [message])

        form_data['uid']='not a number'
        household_form = HouseholdForm(form_data)
        self.assertFalse(household_form.is_valid())
        self.assertEquals(household_form.errors['uid'], ['Enter a whole number.'])

        form_data['uid']= None
        household_form = HouseholdForm(form_data)
        self.assertFalse(household_form.is_valid())
        self.assertEquals(household_form.errors['uid'], ['This field is required.'])


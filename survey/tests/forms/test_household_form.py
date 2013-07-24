from django.test import TestCase
from survey.forms.household import *
from survey.models import Investigator, Backend

class HouseholdFormTest(TestCase):

    def test_valid(self):
        form_data = {
                        'number_of_males': '6',
                        'number_of_females': '6',
                    }
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
                        'number_of_males': -6,
                        'number_of_females': 6,
                    }
        household_form = HouseholdForm(form_data)
        self.assertFalse(household_form.is_valid())
        message = "Ensure this value is greater than or equal to 0."
        self.assertEquals(household_form.errors['number_of_males'], [message])

        form_data['number_of_females']='not a number'
        household_form = HouseholdForm(form_data)
        self.assertFalse(household_form.is_valid())
        self.assertEquals(household_form.errors['number_of_females'], ['Enter a whole number.'])

        form_data['number_of_females']= None
        household_form = HouseholdForm(form_data)
        self.assertFalse(household_form.is_valid())
        self.assertEquals(household_form.errors['number_of_females'], ['This field is required.'])


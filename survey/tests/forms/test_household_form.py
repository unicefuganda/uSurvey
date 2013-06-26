from django.test import TestCase
from survey.forms.household import *
from survey.models import Investigator

class HouseholdFormTest(TestCase):

    def setUp(self):
        pass

    def test_valid(self):
        form_data = {
                        'number_of_males': '6',
                        'number_of_females': '6',
                        'size': '12',
                    }
        household_form = HouseholdForm(form_data)
        self.assertTrue(household_form.is_valid())
        investigator = Investigator.objects.create(name="test")
        household_form.instance.investigator = investigator
        household = household_form.save()
        self.failUnless(household.id)
        household_retrieved = Household.objects.get(investigator=investigator)
        self.assertEqual(household_retrieved, household)

    def test_invalid(self):
        form_data = {
                        'number_of_males': '6',
                        'number_of_females': '6',
                        'size': '0',
                    }
        household_form = HouseholdForm(form_data)
        self.assertFalse(household_form.is_valid())
        message = "Total number of household members does not match female and male ones."
        self.assertEquals(household_form.errors['size'], [message])

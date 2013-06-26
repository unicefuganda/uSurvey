from django.test import TestCase
from survey.forms.householdHead import *
from survey.models import Investigator

class HouseholdHeadFormTest(TestCase):

    def setUp(self):
        self.form_data = {
                        'surname': 'household',
                        'first_name': 'bla',
                        'male': 't',
                        'age':'23',
                        'level_of_education':'Primary',
                        'occupation':'Brewing',
                        'resident_since':'3',
                        'time_measure':'Years',
                    }

    def test_valid(self):
        hHead_form = HouseholdHeadForm(self.form_data)
        self.assertTrue(hHead_form.is_valid())
        household = Household.objects.create()
        hHead_form.instance.household = household
        hHead = hHead_form.save()
        self.failUnless(hHead.id)
        hHead_retrieved = HouseholdHead.objects.get(household=household)
        self.assertEqual(hHead_retrieved, hHead)

    def test_age(self):
        data = self.form_data
        data['age']=9
        hHead_form = HouseholdHeadForm(data)
        self.assertFalse(hHead_form.is_valid())
        message = "Ensure this value is greater than or equal to 10."
        self.assertEquals(hHead_form.errors['age'], [message])

        data['age']=100
        hHead_form = HouseholdHeadForm(data)
        self.assertFalse(hHead_form.is_valid())
        message = "Ensure this value is less than or equal to 99."
        self.assertEquals(hHead_form.errors['age'], [message])


    def test_required_fields(self):
        data = self.form_data
        del data['age']
        del data['surname']
        del data['first_name']

        hHead_form = HouseholdHeadForm(data)
        self.assertFalse(hHead_form.is_valid())
        message = "This field is required."
        self.assertEquals(hHead_form.errors['age'], [message])
        self.assertEquals(hHead_form.errors['surname'], [message])
        self.assertEquals(hHead_form.errors['first_name'], [message])

    def test_positive_resident_since(self):
        data = self.form_data

        data['resident_since'] = -6
        hHead_form = HouseholdHeadForm(data)
        self.assertFalse(hHead_form.is_valid())
        message = "Ensure this value is greater than or equal to 0."
        self.assertEquals(hHead_form.errors['resident_since'], [message])

        data['resident_since'] = 'not a number'
        hHead_form = HouseholdHeadForm(data)
        self.assertFalse(hHead_form.is_valid())
        message = 'Enter a whole number.'
        self.assertEquals(hHead_form.errors['resident_since'], [message])

        data['resident_since'] = None
        hHead_form = HouseholdHeadForm(data)
        self.assertFalse(hHead_form.is_valid())
        message = 'This field is required.'
        self.assertEquals(hHead_form.errors['resident_since'], [message])


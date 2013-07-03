from django.test import TestCase
from survey.forms.women import *
from survey.models import Household

class WomenFormTest(TestCase):

    def setUp(self):
        self.form_data = {
                            'has_women': 'True',
                            'aged_between_15_19_years':'0',
                            'aged_between_20_49_years':'0',
                            }
        self.numeric_fields = ['aged_between_15_19_years', 'aged_between_20_49_years']

    def test_valid(self):
        women_form = WomenForm(self.form_data)
        self.assertTrue(women_form.is_valid())
        household = Household.objects.create()
        women_form.instance.household = household
        women = women_form.save()
        self.failUnless(women.id)
        women_retrieved = Women.objects.get(household=household)
        self.assertEqual(women_retrieved, women)

    def test_negative_numbers(self):
        data = self.form_data

        for field in self.numeric_fields:
            data[field]= -1
            women_form = WomenForm(data)
            self.assertFalse(women_form.is_valid())
            message = "Ensure this value is greater than or equal to 0."
            self.assertEquals(women_form.errors[field], [message])
            data[field] = self.form_data[field]

    def test_not_a_number(self):
        data = self.form_data

        for field in self.numeric_fields:
            data[field]= 'not a number !!! $%&#'
            women_form = WomenForm(data)
            self.assertFalse(women_form.is_valid())
            message = "Enter a whole number."
            self.assertEquals(women_form.errors[field], [message])
            data[field] = self.form_data[field]

    def test_required(self):
        data = self.form_data

        for field in self.numeric_fields:
            data[field]= None
            women_form = WomenForm(data)
            self.assertFalse(women_form.is_valid())
            message = "This field is required."
            self.assertEquals(women_form.errors[field], [message])
            data[field] = self.form_data[field]

    def test_has_women_false_but_one_of_the_field_positive(self):
        data = self.form_data
        data['has_women']= 'False'

        for field in self.numeric_fields:
            data[field]= 1
            women_form = WomenForm(data)
            self.assertFalse(women_form.is_valid())
            message = "Should be zero. This household has no women aged 15+ years."
            self.assertEquals(women_form.errors[field], [message])
            data[field] = self.form_data[field]

    def test_has_women_true_but_total_number_of_females_is_0(self):
        data = self.form_data
        household = Household(number_of_females=0)
        women = Women(household=household)
        women_form = WomenForm(data, instance=women)
        self.assertFalse(women_form.is_valid())
        message = "Should be No. The number of females in this household is 0."
        self.assertEquals(women_form.errors['has_women'], [message])




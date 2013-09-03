from django.test import TestCase
from survey.forms.children import *
from survey.models import Household

class ChildrenFormTest(TestCase):

    def setUp(self):
        self.form_data = {
                            'has_children':'True',
                            'has_children_below_5':'True',
                            'total_below_5':0,
                            'aged_between_5_12_years': 0,
                            'aged_between_13_17_years':0,
                            'aged_between_0_5_months':0,
                            'aged_between_6_11_months':0,
                            'aged_between_12_23_months':0,
                            'aged_between_24_59_months':0,
                            }
        self.numeric_fields = ['aged_between_5_12_years', 'aged_between_13_17_years', 'aged_between_0_5_months',
                              'aged_between_6_11_months', 'aged_between_12_23_months', 'aged_between_24_59_months']
        self.below_5_fields = ['aged_between_0_5_months', 'aged_between_6_11_months',
                                              'aged_between_12_23_months', 'aged_between_24_59_months']

    def test_valid(self):
        children_form = ChildrenForm(self.form_data)
        self.assertTrue(children_form.is_valid())
        household = Household.objects.create(uid=1)
        children_form.instance.household = household
        children = children_form.save()
        self.failUnless(children.id)
        children_retrieved = Children.objects.get(household=household)
        self.assertEqual(children_retrieved, children)

    def test_negative_numbers(self):
        data = self.form_data

        for field in self.numeric_fields:
            data[field]= -1
            children_form = ChildrenForm(data)
            self.assertFalse(children_form.is_valid())
            message = "Ensure this value is greater than or equal to 0."
            self.assertEquals(children_form.errors[field], [message])
            data[field] = self.form_data[field]

    def test_not_a_number(self):
        data = self.form_data

        for field in self.numeric_fields:
            data[field]= 'not a number !!! $%&#'
            children_form = ChildrenForm(data)
            self.assertFalse(children_form.is_valid())
            message = "Enter a whole number."
            self.assertEquals(children_form.errors[field], [message])
            data[field] = self.form_data[field]

    def test_required(self):
        data = self.form_data

        for field in self.numeric_fields:
            data[field]= None
            children_form = ChildrenForm(data)
            self.assertFalse(children_form.is_valid())
            message = "This field is required."
            self.assertEquals(children_form.errors[field], [message])
            data[field] = self.form_data[field]

    def test_has_children_false_but_one_of_the_field_positive(self):
        data = self.form_data
        data['has_children']= 'False'

        for field in self.numeric_fields:
            data[field]= 1
            children_form = ChildrenForm(data)
            self.assertFalse(children_form.is_valid())
            message = "Should be zero. This household has no children."
            self.assertEquals(children_form.errors[field], [message])
            data[field] = self.form_data[field]

    def test_has_children_below_5_false_but_one_of_the_field_positive(self):
        data = self.form_data
        data['has_children_below_5']= 'False'
        for field in self.below_5_fields:
            data[field]= 1
            children_form = ChildrenForm(data)
            self.assertFalse(children_form.is_valid())
            message = "Should be zero. This household has no children below 5 years."
            self.assertEquals(children_form.errors[field], [message])
            data[field] = self.form_data[field]

    def test_has_both_children_and_below_5_false_with_two_separate_fields_positive(self):
        data = self.form_data
        data['has_children']= 'False'
        data['has_children_below_5']= 'False'
        data['aged_between_0_5_months']= 1
        data['aged_between_5_12_years']= 1
        children_form = ChildrenForm(data)
        self.assertFalse(children_form.is_valid())
        message = "Should be zero. This household has no children below 5 years."
        self.assertEquals(children_form.errors['aged_between_0_5_months'], [message])
        message = "Should be zero. This household has no children."
        self.assertEquals(children_form.errors['aged_between_5_12_years'], [message])

    def test_has_both_children_and_below_5_false_with_one_common_field_positive(self):
        data = self.form_data
        data['has_children']= 'False'
        data['has_children_below_5']= 'False'
        data['aged_between_0_5_months']= 1
        children_form = ChildrenForm(data)
        self.assertFalse(children_form.is_valid())
        message = "Should be zero. This household has no children below 5 years."
        self.assertEquals(children_form.errors['aged_between_0_5_months'], [message])

    def test_check_total_below_5(self):
        data = self.form_data
        data['has_children']='True'
        data['has_children_below_5']= 'True'
        data['total_below_5']=5
        for field in self.below_5_fields:
            data[field]= 100
            children_form = ChildrenForm(data)
            self.assertFalse(children_form.is_valid())
            message = "Total does not match."
            self.assertEquals(children_form.errors['total_below_5'], [message])
            data[field] = self.form_data[field]

    def test_check_total_below_5_when_one_of_the_below_5_field_is_not_clean(self):
        data = self.form_data
        data['has_children']='True'
        data['has_children_below_5']= 'True'
        data['total_below_5']=5
        for field in self.below_5_fields:
            data[field]= 'not a number'
            children_form = ChildrenForm(data)
            self.assertFalse(children_form.is_valid())
            message = "Enter a whole number."
            self.assertEquals(children_form.errors[field], [message])
            self.assertFalse(children_form.errors.has_key('total_below_5'))
            data[field] = self.form_data[field]

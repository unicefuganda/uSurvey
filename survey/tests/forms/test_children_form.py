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

    def test_valid(self):
        children_form = ChildrenForm(self.form_data)
        print children_form.errors
        self.assertTrue(children_form.is_valid())
        household = Household.objects.create()
        children_form.instance.household = household
        children = children_form.save()
        self.failUnless(children.id)
        children_retrieved = Children.objects.get(household=household)
        self.assertEqual(children_retrieved, children)

    def test_has_children_false_but_one_of_the_field_positive(self):
        data = self.form_data
        data['has_children']= 'False'

        for field in ['aged_between_5_12_years', 'aged_between_13_17_years', 'aged_between_0_5_months',
                    'aged_between_6_11_months', 'aged_between_12_23_months', 'aged_between_24_59_months']:
            data[field]= 1
            children_form = ChildrenForm(data)
            self.assertFalse(children_form.is_valid())
            message = "Should be zero. This household has no children."
            self.assertEquals(children_form.errors[field], [message])

    #     data['age']=100
    #     children_form = ChildrenForm(data)
    #     self.assertFalse(children_form.is_valid())
    #     message = "Ensure this value is less than or equal to 99."
    #     self.assertEquals(children_form.errors['age'], [message])
    #
    #
    # def test_required_fields(self):
    #     data = self.form_data
    #     del data['age']
    #     del data['surname']
    #     del data['first_name']
    #
    #     children_form = ChildrenForm(data)
    #     self.assertFalse(children_form.is_valid())
    #     message = "This field is required."
    #     self.assertEquals(children_form.errors['age'], [message])
    #     self.assertEquals(children_form.errors['surname'], [message])
    #     self.assertEquals(children_form.errors['first_name'], [message])
    #
    # def test_positive_resident_since(self):
    #     data = self.form_data
    #
    #     data['resident_since'] = -6
    #     children_form = ChildrenForm(data)
    #     self.assertFalse(children_form.is_valid())
    #     message = "Ensure this value is greater than or equal to 0."
    #     self.assertEquals(children_form.errors['resident_since'], [message])
    #
    #     data['resident_since'] = 'not a number'
    #     children_form = ChildrenForm(data)
    #     self.assertFalse(children_form.is_valid())
    #     message = 'Enter a whole number.'
    #     self.assertEquals(children_form.errors['resident_since'], [message])
    #
    #     data['resident_since'] = None
    #     children_form = ChildrenForm(data)
    #     self.assertFalse(children_form.is_valid())
    #     message = 'This field is required.'
    #     self.assertEquals(children_form.errors['resident_since'], [message])


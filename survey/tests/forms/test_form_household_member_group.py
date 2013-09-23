from django.test import TestCase
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition
from survey.forms.household_member_group import HouseholdMemberGroupForm


class HouseholdMemberGroupTests(TestCase):
    def setUp(self):
        self.group_condition = GroupCondition.objects.create(condition='haha', value="True", attribute="hmm")
        self.group_condition_2 = GroupCondition.objects.create(condition='another', value="True", attribute="hmm")
        self.form_data = {
            'name': "5 to 12 years",
            'order': 1,
            'conditions': [self.group_condition.id, self.group_condition_2.id]
        }

    def test_valid(self):
        form_data = self.form_data
        household_member_group_form = HouseholdMemberGroupForm(form_data)
        self.assertTrue(household_member_group_form.is_valid())

    def test_invalid_group_exists(self):
        household_member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=7)

        form_data = {
            'name': household_member_group.name,
            'order': household_member_group.order,
            'conditions': [self.group_condition.id]
        }

        household_member_group_form = HouseholdMemberGroupForm(form_data)
        self.assertFalse(household_member_group_form.is_valid())
        self.assertEquals(1, len(household_member_group_form.errors))
        self.assertTrue(household_member_group_form.errors.has_key('order'))
        expected_form_error = 'This order already exists. The minimum available is %d.'% (HouseholdMemberGroup.max_order()+1)
        self.assertEqual(household_member_group_form.errors['order'][0], expected_form_error)

    def test_invalid_given_empty_fields_present(self):

        form_field_keys = ['name', 'order', 'conditions']
        form_data = {
            'name': '',
            'order': '',
            'conditions': []
        }

        household_member_group_form = HouseholdMemberGroupForm(form_data)
        self.assertFalse(household_member_group_form.is_valid())
        self.assertEquals(3, len(household_member_group_form.errors))
        [self.assertTrue(household_member_group_form.errors.has_key(form_key)) for form_key in form_field_keys]

    def test_negative_order(self):
        form_data = self.form_data
        form_data['order']= -1

        household_member_group_form = HouseholdMemberGroupForm(form_data)
        self.assertFalse(household_member_group_form.is_valid())
        self.assertTrue(household_member_group_form.errors.has_key('order'))
        expected_form_error = 'Ensure this value is greater than or equal to 0.'
        self.assertEqual(household_member_group_form.errors['order'][0], expected_form_error)

    def test_NaN_order(self):
        form_data = self.form_data
        form_data['order']= 'Not a Number'

        household_member_group_form = HouseholdMemberGroupForm(form_data)
        self.assertFalse(household_member_group_form.is_valid())
        self.assertTrue(household_member_group_form.errors.has_key('order'))
        expected_form_error = 'Enter a whole number.'
        self.assertEqual(household_member_group_form.errors['order'][0], expected_form_error)

    def test_required_fields(self):
        form_data = self.form_data

        for field in form_data.keys():
            form_data[field]= ''

            household_member_group_form = HouseholdMemberGroupForm(form_data)
            self.assertFalse(household_member_group_form.is_valid())
            self.assertTrue(household_member_group_form.errors.has_key(field))
            expected_form_error = 'This field is required.'
            self.assertEqual(household_member_group_form.errors[field][0], expected_form_error)
            form_data = self.form_data


from django.test import TestCase
from survey.models import HouseholdMemberGroup
from survey.forms.household_member_group import HouseholdMemberGroupForm


class HouseholdMemberGroupTests(TestCase):
    
    def test_valid(self):
        form_data = {
            'name': "5 to 12 years",
            'order': 1
            }
        
        household_member_group_form = HouseholdMemberGroupForm(form_data)
        print household_member_group_form
        self.assertTrue(household_member_group_form.is_valid())
        
    def test_invalid_group_exists(self):
        household_member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=1)
        
        form_data = {
            'name': household_member_group.name,
            'order': household_member_group.order
            }
        
        household_member_group_form = HouseholdMemberGroupForm(form_data)
        self.assertFalse(household_member_group_form.is_valid())
        self.assertEquals(1, len(household_member_group_form.errors))
        self.assertTrue(household_member_group_form.errors.has_key('order'))
        expected_form_error = 'Household member group with this Order already exists.'
        self.assertEqual(household_member_group_form.errors['order'][0], expected_form_error)
from django.test import TestCase
from survey.forms.group_condition import GroupConditionForm


class GroupConditionFormTests(TestCase):
    
    
    def test_valid_form(self):
        form_data = {
            'value' : 3,
            'attribute': "AGE",
            'condition': 'GREATER_THAN'
        }
        
        group_condition_form = GroupConditionForm(form_data)
        self.assertTrue(group_condition_form.is_valid())
        
    def test_valid_form_due_to_invalid_condition(self):
        form_data = {
            'value' : 3,
            'attribute': "AGE",
            'condition': 'GREATER'
        }

        group_condition_form = GroupConditionForm(form_data)
        self.assertFalse(group_condition_form.is_valid())
        self.assertEqual(1, len(group_condition_form.errors))
        self.assertTrue(group_condition_form.errors.has_key("condition"))
        invalid_condition_choice = "Select a valid choice. GREATER is not one of the available choices."
        self.assertEqual(group_condition_form.errors["condition"][0], invalid_condition_choice)

    def test_valid_form_due_to_empty_fields_present(self):
        form_field_keys = ['value', 'attribute', 'condition']
        form_data = {
            'value': '',
            'attribute': "",
            'condition': ''
        }

        group_condition_form = GroupConditionForm(form_data)
        self.assertFalse(group_condition_form.is_valid())
        self.assertEqual(3, len(group_condition_form.errors))
        [self.assertTrue(group_condition_form.errors.has_key(key)) for key in form_field_keys]
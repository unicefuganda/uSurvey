from django.test import TestCase
from survey.models.householdgroups import GroupCondition
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

    def test_invalid_value_which_is_not_an_integer_form(self):
        form_data = {
            'value' : 0.1,
            'attribute': "AGE",
            'condition': 'GREATER_THAN'
        }

        group_condition_form = GroupConditionForm(form_data)
        self.assertFalse(group_condition_form.is_valid())

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

    def test_gender_only_accepts_equal_condition(self):
        form_data = {
            'value': 'Male',
            'attribute': GroupCondition.GROUP_TYPES['GENDER'],
            'condition': GroupCondition.CONDITIONS['GREATER_THAN'],
        }

        group_condition_form = GroupConditionForm(form_data)
        self.assertFalse(group_condition_form.is_valid())

        message = "GENDER can only have condition: EQUALS."
        self.assertEqual([message], group_condition_form.errors['condition'])

    def test_gender_only_accepts_male_or_female_values(self):
        form_data = {
            'value': 'not Male',
            'attribute': GroupCondition.GROUP_TYPES['GENDER'],
            'condition': GroupCondition.CONDITIONS['EQUALS'],
        }

        group_condition_form = GroupConditionForm(form_data)
        self.assertFalse(group_condition_form.is_valid())
        message = "GENDER can only have male or female values."
        self.assertEqual([message], group_condition_form.errors['value'])

    def test_age_should_be_positive(self):
        form_data = {
            'value': '-3',
            'attribute': GroupCondition.GROUP_TYPES['AGE'],
            'condition': GroupCondition.CONDITIONS['EQUALS'],
        }

        group_condition_form = GroupConditionForm(form_data)
        self.assertFalse(group_condition_form.is_valid())
        message = "Age cannot be negative."
        self.assertEqual([message], group_condition_form.errors['value'])

    # def test_general_only_accepts_equal_condition(self):
    #     form_data = {
    #         'value': 'HEAD',
    #         'attribute': GroupCondition.GROUP_TYPES['GENERAL'],
    #         'condition': GroupCondition.CONDITIONS['GREATER_THAN'],
    #     }
    #
    #     group_condition_form = GroupConditionForm(form_data)
    #     self.assertFalse(group_condition_form.is_valid())
    #     message = "GENERAL can only have condition: EQUALS."
    #     self.assertEqual([message], group_condition_form.errors['condition'])

    # def test_general_only_accepts_head_as_value(self):
    #     form_data = {
    #         'value': 'not HEAD',
    #         'attribute': GroupCondition.GROUP_TYPES['GENERAL'],
    #         'condition': GroupCondition.CONDITIONS['EQUALS'],
    #     }
    #
    #     group_condition_form = GroupConditionForm(form_data)
    #     self.assertFalse(group_condition_form.is_valid())
    #     message = "GENERAL can only have the value: HEAD."
    #     self.assertEqual([message], group_condition_form.errors['value'])
    #
    # def test_validates_unqique_constraint_on_group_condition(self):
    #     form_data = {
    #         'value': 'HEAD',
    #         'attribute': GroupCondition.GROUP_TYPES['GENERAL'],
    #         'condition': GroupCondition.CONDITIONS['EQUALS'],
    #     }
    #
    #     group_condition_form = GroupConditionForm(form_data)
    #     self.assertTrue(group_condition_form.is_valid())
    #     group_condition_form.save()
    #
    #     duplicate_data = {
    #         'value': 'HEAD',
    #         'attribute': GroupCondition.GROUP_TYPES['GENERAL'],
    #         'condition': GroupCondition.CONDITIONS['EQUALS'],
    #         }
    #
    #     duplicate_group_condition_form = GroupConditionForm(duplicate_data)
    #     self.assertFalse(duplicate_group_condition_form.is_valid())
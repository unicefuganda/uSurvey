from django.test import TestCase
from survey.models.householdgroups import GroupCondition


class GroupConditionTest(TestCase):

    def test_fields(self):
        group_condition = GroupCondition()
        fields = [str(item.attname) for item in group_condition._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created', 'modified', 'value', 'attribute', 'condition']:
            self.assertIn(field, fields)

    def test_store(self):
        hmg = GroupCondition.objects.create(value="some string")
        self.failUnless(hmg.id)
        self.failUnless(hmg.created)
        self.failUnless(hmg.modified)
        self.assertEquals("some string", hmg.value)
        self.assertEquals("EQUALS", hmg.condition)

    def test_store_boolean_value(self):
        hmg = GroupCondition.objects.create(value=True)
        self.assertTrue(hmg.value)

    def test_store_numeric_value(self):
        hmg = GroupCondition.objects.create(value=5)
        self.assertEquals(5, hmg.value)

    def test_knows_age_condition_equal_to_a_specific_value(self):
        age_value = 20
        attribute_type = "age"
        age_condition = GroupCondition.objects.create(attribute=attribute_type, value=age_value)

        self.assertTrue(age_condition.matches_condition(age_value))

    def test_knows_age_condition_not_equal_to_a_specific_value(self):
        age_value = 20
        attribute_type = "age"
        age_condition = GroupCondition.objects.create(attribute=attribute_type, value=age_value)

        self.assertFalse(age_condition.matches_condition(age_value + 2))

    def test_knows_to_match_greater_than_condition(self):
        age_value = 20
        attribute_type = "age"
        age_condition = GroupCondition.objects.create(attribute=attribute_type, value=age_value, condition='GREATER_THAN')

        self.assertTrue(age_condition.matches_condition(age_value+2))

    def test_knows_to_match_greater_than_condition_if_condition_is_not_met(self):
        age_value = 20
        attribute_type = "age"
        age_condition = GroupCondition.objects.create(attribute=attribute_type, value=age_value, condition='GREATER_THAN')

        self.assertFalse(age_condition.matches_condition(age_value-2))

    def test_knows_to_match_less_than_condition(self):
        age_value = 20
        attribute_type = "age"
        age_condition = GroupCondition.objects.create(attribute=attribute_type, value=age_value, condition='LESS_THAN')

        self.assertTrue(age_condition.matches_condition(age_value-2))

    def test_knows_to_match_less_than_condition_if_condition_is_not_met(self):
        age_value = 20
        attribute_type = "age"
        age_condition = GroupCondition.objects.create(attribute=attribute_type, value=age_value, condition='LESS_THAN')

        self.assertFalse(age_condition.matches_condition(age_value+2))

    def test_knows_to_match_equal_to_condition_for_gender_if_false(self):
        gender_value = False
        attribute_type = "gender"
        gender_condition = GroupCondition.objects.create(attribute=attribute_type, value=gender_value, condition='EQUALS')

        self.assertTrue(gender_condition.matches_condition(gender_value))
        self.assertFalse(gender_condition.matches_condition(not gender_value))

    def test_knows_to_match_equal_to_condition_for_gender_if_condition_value_is_female(self):
        gender_value = "Female"
        attribute_type = "gender"
        is_male = True
        is_female = False
        gender_condition = GroupCondition.objects.create(attribute=attribute_type, value=gender_value, condition='EQUALS')

        self.assertTrue(gender_condition.matches_condition(is_female))
        self.assertFalse(gender_condition.matches_condition(is_male))

    def test_knows_to_match_equal_to_condition_for_gender_if_condition_value_is_male(self):
        gender_value = "Male"
        attribute_type = "gender"
        is_male = True
        is_female = False
        gender_condition = GroupCondition.objects.create(attribute=attribute_type, value=gender_value, condition='EQUALS')

        self.assertTrue(gender_condition.matches_condition(is_male))
        self.assertFalse(gender_condition.matches_condition(is_female))

    def test_knows_to_match_equal_to_condition_for_general_if_condition_value_is_head(self):
        value = "HEAD"
        attribute_type = "GENERAL"
        is_head = True
        general_condition = GroupCondition.objects.create(attribute=attribute_type, value=value, condition='EQUALS')

        self.assertTrue(general_condition.matches_condition(is_head))

        value = "HEAD"
        attribute_type = "gender"
        is_head = True
        general_condition = GroupCondition.objects.create(attribute=attribute_type, value=value, condition='EQUALS')

        self.assertFalse(general_condition.matches_condition(is_head))

    def test_should_not_match_general_condition_to_head_is_false(self):
        value = "HEAD"
        attribute_type = "GENERAL"
        general_condition = GroupCondition.objects.create(attribute=attribute_type, value=value, condition='EQUALS')

        is_head = False

        self.assertFalse(general_condition.matches_condition(is_head))
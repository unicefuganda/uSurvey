from django.test import TestCase
from survey.models import GroupCondition

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

        
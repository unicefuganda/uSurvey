from django.test import TestCase
from survey.models import GroupConditionMaping, HouseholdMemberGroup, GroupCondition
class GroupConditionMapingTests(TestCase):
    def test_fields(self):
        group_condition_mapping = GroupConditionMaping()
        fields = [str(item.attname) for item in group_condition_mapping._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'household_member_group_id', 'group_condition_id']:
            self.assertIn(field, fields)
            

    def test_store(self):
        group = HouseholdMemberGroup.objects.create(name="some group")
        condition = GroupCondition.objects.create(value=True, attribute="gender", condition="GREATER_THAN")
        groupmapping = GroupConditionMaping.objects.create(household_member_group=group, group_condition=condition)
        self.failUnless(groupmapping.id)
        self.failUnless(groupmapping.created)
        self.failUnless(groupmapping.modified)
        self.assertEquals(group, groupmapping.household_member_group)
        self.assertEquals(condition, groupmapping.group_condition)
        
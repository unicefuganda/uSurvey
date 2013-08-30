from django.test import TestCase
from survey.models import HouseholdMemberGroup, GroupCondition
from survey.forms.group_condition_mapping import GroupConditionMappingForm

class GroupConditionMappingFormTests(TestCase):
    
    def test_valid(self):
        household_member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=1)
        group_condition = GroupCondition.objects.create(value="some string")
        
        form_data = {
            'household_member_group': household_member_group.id,
            'group_condition': group_condition.id
        }
        
        group_condition_mapping_form = GroupConditionMappingForm(form_data)
        self.assertTrue(group_condition_mapping_form.is_valid())
        
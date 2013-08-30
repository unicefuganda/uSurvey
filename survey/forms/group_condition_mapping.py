from django.forms import ModelForm
from survey.models import GroupConditionMaping

class GroupConditionMappingForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(GroupConditionMappingForm, self).__init__(*args, **kwargs)
        
    class Meta:
        model = GroupConditionMaping
        fields = ['household_member_group','group_condition']
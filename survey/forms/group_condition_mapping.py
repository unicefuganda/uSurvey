from django.forms import ModelForm
from survey.models import GroupConditionMaping

class GroupConditionMappingForm(ModelForm):

    class Meta:
        model = GroupConditionMaping
        fields = ['household_member_group','group_condition']
from django.forms import ModelForm
from survey.models.householdgroups import GroupCondition


class GroupConditionForm(ModelForm):

    class Meta:
        model = GroupCondition
        fields =['attribute', 'condition', 'value']
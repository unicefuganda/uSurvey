from django.forms import ModelForm
from survey.models import GroupCondition


class GroupConditionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(GroupConditionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = GroupCondition
        fields =['value','condition']
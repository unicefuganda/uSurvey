from django.forms import ModelForm
from survey.models import GroupCondition


class GroupConditionForm(ModelForm):

    class Meta:
        model = GroupCondition
        fields =['value','condition', 'attribute']
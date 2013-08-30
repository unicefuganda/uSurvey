from django.forms import ModelForm
from survey.models import HouseholdMemberGroup


class HouseholdMemberGroupForm(ModelForm):
    
    class Meta:
        model = HouseholdMemberGroup
        fields =['name','order']
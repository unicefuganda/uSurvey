from django.forms import ModelForm
from survey.models import HouseholdMemberGroup


class HouseholdMemberGroupForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(HouseholdMemberGroupForm, self).__init__(*args, **kwargs)

    class Meta:
        model = HouseholdMemberGroup
        fields =['name','order']
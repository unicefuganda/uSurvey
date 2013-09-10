from django.forms import ModelForm
from survey.models.households import Household


class HouseholdForm(ModelForm):

    class Meta:
        model = Household
        exclude = ['investigator']

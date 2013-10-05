from django.forms import ModelForm
from survey.models.households import Household


class HouseholdForm(ModelForm):
    class Meta:
        model = Household
        exclude = ['investigator', 'location']

    def __init__(self, *args, **kwargs):
        super(HouseholdForm, self).__init__(*args, **kwargs)
        self.fields['uid'].initial = Household.next_uid()
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models.households import Household


class HouseholdForm(ModelForm):
    class Meta:
        model = Household
        exclude = ['investigator', 'location']

    def __init__(self, is_edit=False, *args, **kwargs):
        super(HouseholdForm, self).__init__(*args, **kwargs)
        self.is_editing = is_edit

        if not self.is_editing:
            self.fields['uid'].initial = Household.next_uid()
        else:
            self.fields['uid'].initial = self.instance.uid

    def clean_uid(self):
        uid = self.cleaned_data['uid']
        household = Household.objects.filter(uid=int(uid))
        if not self.is_editing and household:
            raise ValidationError("Household with this Household Unique Identification already exists.")
        elif self.is_editing and self.instance.uid != int(uid):
            raise ValidationError("Household Unique Identification cannot be modified.")
        return self.cleaned_data['uid']
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models.households import Household
from django import forms

class HouseholdForm(ModelForm):
    class Meta:
        model = Household
        exclude = ['investigator', 'location', 'survey', 'household_code']
        widgets = {
            'ea': forms.HiddenInput(),
        }

    def __init__(self, is_edit=False, uid=None,  survey=None, *args, **kwargs):
        super(HouseholdForm, self).__init__(*args, **kwargs)
        self.is_editing = is_edit

        if not self.is_editing:
            self.fields['uid'].initial = Household.next_uid(survey)
        else:
            self.fields['uid'].initial = self.instance.uid
            self.fields['uid'].widget.attrs['disabled'] = 'disabled'

    def clean_uid(self):
        if not self.is_editing:
            try:
                uid = self.cleaned_data['uid']
                household = Household.objects.filter(uid=int(uid))
                if household:
                    raise ValidationError("Household with this Household Unique Identification already exists.")
            except TypeError:
                raise ValidationError("This field is required.")

        return self.cleaned_data['uid']
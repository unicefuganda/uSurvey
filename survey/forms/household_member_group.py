from django.forms import ModelForm
from django import forms
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition


class HouseholdMemberGroupForm(ModelForm):

    conditions = forms.ModelMultipleChoiceField(label=u'Conditions', queryset=GroupCondition.objects.all(),
                                                widget=forms.SelectMultiple(attrs={'class': 'multi-select'}))

    class Meta:
        model = HouseholdMemberGroup

    def __init__(self, *args, **kwargs):
        super(HouseholdMemberGroupForm, self).__init__(*args, **kwargs)
        condition_qs = self.fields['conditions']._queryset
        self.fields['conditions'].choices = [(e.id, "%s > %s > %s" % (e.attribute, e.condition, e.value)) for e in
                                             condition_qs]

    def add_conditions(self, group):
        for condition in self.cleaned_data['conditions']:
            condition.groups.add(group)

    def save(self, commit=True, *args, **kwargs):
        group = super(HouseholdMemberGroupForm, self).save(commit=commit, *args, **kwargs)
        if commit:
            self.add_conditions(group)

        return group
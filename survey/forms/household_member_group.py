from django.forms import ModelForm
from django import forms
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition


class HouseholdMemberGroupForm(ModelForm):

    conditions = forms.ModelMultipleChoiceField(label=u'Eligibility Criteria', queryset=GroupCondition.objects.all(),
                                                widget=forms.SelectMultiple(attrs={'class': 'multi-select'}))

    class Meta:
        model = HouseholdMemberGroup

    def add_conditions(self, group):
        group.conditions.clear()
        for condition in self.cleaned_data['conditions']:
            condition.groups.add(group)

    def save(self, commit=True, *args, **kwargs):
        group = super(HouseholdMemberGroupForm, self).save(commit=commit, *args, **kwargs)
        if commit:
            self.add_conditions(group)
        return group

    def clean_order(self):
        order = self.cleaned_data['order']
        if HouseholdMemberGroup.objects.filter(order=order).count()>0 and self.initial.get('order', None) != int(order):
            message = 'This order already exists. The minimum available is %d.'% (HouseholdMemberGroup.max_order()+1)
            self._errors['order'] = self.error_class([message])
            del self.cleaned_data['order']
        return order
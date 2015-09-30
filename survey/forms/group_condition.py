from django.forms import ModelForm
from django import forms
from survey.models.householdgroups import GroupCondition


class GroupConditionForm(ModelForm):
    
    def clean_gender_condition(self):
        self.condition_should_be_equal_for('GENDER')

    def clean_general_condition(self):
        self.condition_should_be_equal_for('GENERAL')

    def condition_should_be_equal_for(self, attribute_str):
        if self.cleaned_data.get('condition', None) and self.cleaned_data.get('attribute', None):
            condition = self.cleaned_data['condition']
            attribute = self.cleaned_data['attribute']

            if attribute == GroupCondition.GROUP_TYPES[attribute_str] and condition != GroupCondition.CONDITIONS['EQUALS']:
                message = "%s can only have condition: %s."% (GroupCondition.GROUP_TYPES[attribute_str], GroupCondition.CONDITIONS['EQUALS'])
                self._errors['condition'] = self.error_class([message])
                del self.cleaned_data['condition']
            return self.cleaned_data

    def clean_gender_values(self):
        if self.cleaned_data.get('condition', None) and self.cleaned_data.get('value', None):
            value = self.cleaned_data['value']
            attribute = self.cleaned_data['attribute']

            if attribute == GroupCondition.GROUP_TYPES['GENDER'] and str(value) not in ['1', '0']:
                message = "%s can only have male or female values." % GroupCondition.GROUP_TYPES['GENDER']
                self._errors['value'] = self.error_class([message])
                del self.cleaned_data['value']
            return self.cleaned_data

    def set_value_error_message(self, message):
        self._errors['value'] = self.error_class([message])
        del self.cleaned_data['value']

    def clean_age_values(self):
        if self.cleaned_data.get('condition', None) and self.cleaned_data.get('value', None):
            value = self.cleaned_data['value']
            attribute = self.cleaned_data['attribute']

            if attribute == GroupCondition.GROUP_TYPES['AGE']:
                try:
                    if int(value) < 0:
                        message = "Age cannot be negative."
                        self.set_value_error_message(message)
                except ValueError:
                        message = "Age must be a whole number."
                        self.set_value_error_message(message)

            return self.cleaned_data

    def clean_general_values(self):
        if self.cleaned_data.get('condition', None) and self.cleaned_data.get('value', None):
            value = self.cleaned_data['value']
            attribute = self.cleaned_data['attribute']

            if attribute == GroupCondition.GROUP_TYPES['GENERAL'] and value != 'HEAD':
                message = "%s can only have the value: HEAD." % GroupCondition.GROUP_TYPES['GENERAL']
                self._errors['value'] = self.error_class([message])
                del self.cleaned_data['value']
            return self.cleaned_data

    def clean(self):
        self.clean_gender_values()
        self.clean_age_values()
        self.clean_gender_condition()
        self.clean_general_values()
        self.clean_general_condition()
        self.cleaned_data = super(GroupConditionForm, self).clean()        
        return self.cleaned_data
        
    class Meta:
        model = GroupCondition
        fields =['attribute', 'condition', 'value']
        widgets = {
            'value': forms.TextInput(attrs={'type':'number', 'min':0, 'max':100}),
        }
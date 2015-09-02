from django import forms
from django.core.exceptions import ValidationError
from survey.models import Answer, MultiChoiceAnswer, MultiSelectAnswer
from survey.models.helper_constants import CONDITIONS


class LogicForm(forms.Form):
    def __init__(self, data=None, initial=None, question=None):
        super(LogicForm, self).__init__(data=data, initial=initial)
        batch = question.batch
        ACTIONS = {
            'END_INTERVIEW': 'END INTERVIEW',
            'SKIP_TO': 'SKIP TO',
            'REANSWER': 'RECONFIRM',
            'ASK_SUBQUESTION': 'ASK SUBQUESTION',
        }

        self.fields['action'].choices = ACTIONS.items()
        self.fields['condition'].choices = [(validator.__name__, validator.__name__.upper()) \
                                           for validator in Answer.get_class(question.answer_type).validators()]
        self.fields['attribute'].choices = [(validator.__name__, getattr(validator.label.upper() or validator.__name__) \
                                           for validator in Answer.get_class(question.answer_type).validators()]
        self.question = question
        self.batch = batch
        action_sent = data.get('action', None) if data else None

    def choices_for_condition_field(self, is_multichoice):
        condition_choices = {}
        for key, value in CONDITIONS.items():
            is_equals_option = (key == 'EQUALS_OPTION')
            if (is_equals_option and is_multichoice) or (not is_equals_option and not is_multichoice):
                condition_choices[key] = value
        return sorted(condition_choices.items())

    def clean_value(self):
        if (self.cleaned_data['attribute'] == 'value') and (self.cleaned_data['condition'] != 'BETWEEN') and len(self.cleaned_data['value'].strip()) == 0:
            raise ValidationError("Field is required.")
        return self.cleaned_data['value']

    def clean_min_value(self):
        if (self.cleaned_data['condition'] == 'BETWEEN') and len(self.cleaned_data['min_value'].strip()) == 0:
            raise ValidationError("Field is required.")
        return self.cleaned_data['min_value']

    def clean_max_value(self):
        if (self.cleaned_data['condition'] == 'BETWEEN') and len(self.cleaned_data['max_value'].strip()) == 0:
            raise ValidationError("Field is required.")
        return self.cleaned_data['max_value']

    def clean(self):
        field_name = ""
        rule = []

        if self.question.answer_type in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer.choice_name()] :
            #rule = AnswerRule.objects.filter(batch=self.batch, question=self.question, validate_with_option=self.data['option'])
            field_name = 'option'
        else:
            if self.data.get('value',None):
                #rule = AnswerRule.objects.filter(batch=self.batch, question=self.question, validate_with_value=self.data['value'], condition=self.data['condition'])
                field_name = 'value with %s criteria' %self.data['condition']
            elif self.data.get('validate_with_question',None):
                #rule = AnswerRule.objects.filter(batch=self.batch, question=self.question, validate_with_question=self.data['validate_with_question'], condition=self.data['condition'])
                field_name = 'question value with %s criteria' %self.data['condition']

            if not self._validate_max_greater_than_min():
                raise ValidationError('Logic not created max value must be greater than min value.')

            field_name, rule = self._validate_min_value(field_name, rule)
            field_name, rule = self._validate_max_value(field_name, rule)
            field_name, rule = self._validate_min_and_max_range(field_name, rule)

        if len(rule)>0:
            if rule[0] == 1:
                raise ValidationError(field_name)

            raise ValidationError("Rule on this %s already exists." % field_name)
        return self.cleaned_data

    condition = forms.ChoiceField(label='Eligibility criteria', choices=[], widget=forms.Select,
                                  required=False)
    attribute = forms.ChoiceField(label='Attribute', choices=[], widget=forms.Select, required=False)
    option = forms.ChoiceField(label='', choices=[], widget=forms.Select, required=True)
    value = forms.CharField(label='', required=False)
    min_value = forms.CharField(label='', required=False,widget=forms.TextInput(attrs={'placeholder': 'Min Value'}))
    max_value = forms.CharField(label='', required=False,widget=forms.TextInput(attrs={'placeholder': 'Max Value'}))
    # validate_with_question = forms.ChoiceField(label='', choices=[], widget=forms.Select, required=False)
    action = forms.ChoiceField(label='Then', choices=[], widget=forms.Select, required=True)
    next_question = forms.ChoiceField(label='', choices=[], widget=forms.Select, required=False)
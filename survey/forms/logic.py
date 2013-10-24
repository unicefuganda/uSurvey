from django import forms
from django.core.exceptions import ValidationError
from survey.models import AnswerRule
from survey.models.helper_constants import CONDITIONS


class LogicForm(forms.Form):
    def __init__(self, data=None, initial=None, question=None, batch=None):
        super(LogicForm, self).__init__(data=data, initial=initial)
        ACTIONS = {
            'END_INTERVIEW': 'END INTERVIEW',
            'SKIP_TO': 'JUMP TO',
            'REANSWER': 'REANSWER',
            'ASK_SUBQUESTION': 'ASK SUBQUESTION',
        }

        self.fields['action'].choices = ACTIONS.items()
        self.question = question
        self.batch = batch
        action_sent = data.get('action', None) if data else None

        if batch and question:
            is_multichoice = question.is_multichoice()
            self.fields['condition'].choices = self.choices_for_condition_field(is_multichoice)
            question_choices = []
            for next_question in batch.all_questions():
                if next_question.id != question.id:
                    question_choices.append((next_question.id, next_question.text))

            if is_multichoice:
                del self.fields['value']
                del self.fields['min_value']
                del self.fields['max_value']
                del self.fields['validate_with_question']

                all_options = question.options.all()
                self.fields['option'].choices = map(lambda option: (option.id, option.text), all_options)
                self.fields['attribute'].choices = [('option', 'Option')]
            else:
                del self.fields['option']
                self.fields['attribute'].choices = [('value', 'Value'), ('validate_with_question', "Question")]
                self.fields['condition'].initial = 'EQUALS'
                self.fields['validate_with_question'].choices = question_choices

            if action_sent and action_sent == 'ASK_SUBQUESTION':
                question_choices = map(lambda next_question: (next_question.id, next_question.text), question.get_subquestions())

            self.fields['next_question'].choices = question_choices

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

    def _validate_max_value(self, field_name, rule):
        if self.data.get('max_value', None) and not rule:
            try:
                max_value = int(self.data['max_value'])
                rule = AnswerRule.objects.filter(batch=self.batch, question=self.question,
                                             validate_with_min_value__lte=self.data['max_value'],
                                             validate_with_max_value__gte=self.data['max_value'],
                                             condition=self.data['condition'])
                field_name = 'condition %s with max value %s is within existing range that' % (
                    self.data['condition'], self.data['max_value'])
            except ValueError:
                rule = [1]
                field_name = 'Max value %s invalid, must be an integer.' % (self.data['max_value'])

        return field_name, rule

    def _validate_min_value(self, field_name, rule):
        if self.data.get('min_value', None):
            try:
                min_value = int(self.data['min_value'])
                rule = AnswerRule.objects.filter(batch=self.batch, question=self.question,
                                             validate_with_min_value__lte=self.data['min_value'],
                                             validate_with_max_value__gte=self.data['min_value'],
                                             condition=self.data['condition'])
                field_name = 'condition %s with min value %s is within existing range that' % (self.data['condition'], self.data['min_value'])
            except ValueError:
                rule = [1]
                field_name = 'Min value %s invalid, must be an integer.' % (self.data['min_value'])

        return field_name, rule

    def _validate_min_and_max_range(self, field_name, rule):
        if self.data.get('max_value', None) and self.data.get('min_value', None) and not rule:
            rule = AnswerRule.objects.filter(batch=self.batch, question=self.question,
                                             validate_with_min_value__gte=self.data['min_value'],
                                             validate_with_max_value__lte=self.data['max_value'],
                                             condition=self.data['condition'])
            field_name = 'condition %s within range %s - %s' % (self.data['condition'], self.data['min_value'], self.data['max_value'])
        return field_name, rule

    def _validate_max_greater_than_min(self):
      minimum_value = self.data.get('min_value', None)
      maximum_value = self.data.get('max_value', None)

      if minimum_value and maximum_value:
        return int(maximum_value) > int(minimum_value)
      return True

    def clean(self):
        field_name = ""
        rule = []

        if self.question.is_multichoice():
            rule = AnswerRule.objects.filter(batch=self.batch, question=self.question, validate_with_option=self.data['option'])
            field_name = 'option'
        else:
            if self.data.get('value',None):
                rule = AnswerRule.objects.filter(batch=self.batch, question=self.question, validate_with_value=self.data['value'], condition=self.data['condition'])
                field_name = 'value with %s criteria' %self.data['condition']
            elif self.data.get('validate_with_question',None):
                rule = AnswerRule.objects.filter(batch=self.batch, question=self.question, validate_with_question=self.data['validate_with_question'], condition=self.data['condition'])
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
    validate_with_question = forms.ChoiceField(label='', choices=[], widget=forms.Select, required=False)
    action = forms.ChoiceField(label='Then', choices=[], widget=forms.Select, required=True)
    next_question = forms.ChoiceField(label='', choices=[], widget=forms.Select, required=False)
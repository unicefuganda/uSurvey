from django import forms
from survey.models import AnswerRule


class LogicForm(forms.Form):

    def __init__(self, data=None, initial=None, question=None):
        super(LogicForm, self).__init__(data=data, initial=initial)
        ACTIONS = {
            'END_INTERVIEW': 'END INTERVIEW',
            'SKIP_TO': 'JUMP TO',
            'REANSWER': 'REANSWER',
            'ASK_SUBQUESTION': 'ASK SUBQUESTION',
            }

        self.fields['action'].choices = ACTIONS.items()

        if question:
            self.fields['condition'].label = "If %s" % question.text
            is_multichoice = question.is_multichoice()
            self.fields['condition'].choices = self.choices_for_condition_field(is_multichoice)
            question_choices = []
            for next_question in question.batch.all_questions():
                if next_question.id != question.id:
                    question_choices.append((next_question.id, next_question.text))


            if is_multichoice:
                del self.fields['value']
                del self.fields['validate_with_question']

                all_options = question.options.all()
                self.fields['option'].choices = map(lambda option: (option.id, option.text), all_options)
                self.fields['attribute'].choices = [('option', 'Option')]
            else:
                del self.fields['option']
                self.fields['attribute'].choices = [('value', 'Value'), ('validate_with_question', "Question")]
                self.fields['condition'].initial = 'EQUALS'
                self.fields['validate_with_question'].choices = question_choices

            self.fields['next_question'].choices = question_choices

    def choices_for_condition_field(self, is_multichoice):
        condition_choices = {}
        for key, value in AnswerRule.CONDITIONS.items():
            is_equals_option = (key == 'EQUALS_OPTION')
            if (is_equals_option and is_multichoice) or (not is_equals_option and not is_multichoice):
                condition_choices[key] = value
        return condition_choices.items()


    condition = forms.ChoiceField(label='If', choices=AnswerRule.CONDITIONS.items(), widget=forms.Select, required=False)
    attribute = forms.ChoiceField(label='Attribute', choices=[], widget=forms.Select, required=False)
    option = forms.ChoiceField(label='', choices=[], widget=forms.Select, required=True)
    value = forms.CharField(label='', required=False)
    validate_with_question = forms.ChoiceField(label='', choices=[], widget=forms.Select, required=False)
    action = forms.ChoiceField(label='Then', choices=[], widget=forms.Select, required=True)
    next_question = forms.ChoiceField(label='', choices=[], widget=forms.Select, required=False)
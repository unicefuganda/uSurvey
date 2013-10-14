from django.core.exceptions import ValidationError
from django import forms
from survey.models import HouseholdMemberGroup, QuestionModule, Question


class QuestionFilterForm(forms.Form):

    groups = forms.ChoiceField(label='Group', widget=forms.Select(), choices=[])
    modules = forms.ChoiceField(label='Module', widget=forms.Select(), choices=[])
    question_types = forms.ChoiceField(label='Question Type', widget=forms.Select(), choices=[])

    def __init__(self, data=None,initial=None):
        super(QuestionFilterForm, self).__init__(data=data, initial=initial)
        group_choices = [('All', 'All')]
        module_choices = [('All', 'All')]
        question_type_choices = [('All', 'All')]
        map(lambda group: group_choices.append((group.id, group.name)), HouseholdMemberGroup.objects.all())
        map(lambda question_module: module_choices.append((question_module.id, question_module.name)), QuestionModule.objects.all())
        map(lambda question_type: question_type_choices.append(question_type), list(Question.TYPE_OF_ANSWERS))

        self.fields['groups'].choices = group_choices
        self.fields['modules'].choices = module_choices
        self.fields['question_types'].choices = question_type_choices
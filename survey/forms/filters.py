from django.core.exceptions import ValidationError
from django import forms
from survey.models import HouseholdMemberGroup, QuestionModule, Question, Batch, Survey


class QuestionFilterForm(forms.Form):

    groups = forms.ChoiceField(label='Group', widget=forms.Select(), choices=[])
    modules = forms.ChoiceField(label='Module', widget=forms.Select(), choices=[])
    question_types = forms.ChoiceField(label='Question Type', widget=forms.Select(), choices=[])

    def __init__(self, data=None,initial=None):
        super(QuestionFilterForm, self).__init__(data=data, initial=initial)
        group_choices = [('All', 'All')]
        module_choices = [('All', 'All')]
        question_type_choices = [('All', 'All')]
        map(lambda group: group_choices.append((group.id, group.name)), HouseholdMemberGroup.objects.all().exclude(name='REGISTRATION GROUP'))
        map(lambda question_module: module_choices.append((question_module.id, question_module.name)), QuestionModule.objects.all())
        map(lambda question_type: question_type_choices.append(question_type), list(Question.TYPE_OF_ANSWERS))

        self.fields['groups'].choices = group_choices
        self.fields['modules'].choices = module_choices
        self.fields['question_types'].choices = question_type_choices


class IndicatorFilterForm(forms.Form):
    survey = forms.ChoiceField(label='Survey', widget=forms.Select(attrs={'id': 'id_filter_survey'}), choices=[])
    batch = forms.ChoiceField(label='Batch', widget=forms.Select(), choices=[])
    module = forms.ChoiceField(label='Module', widget=forms.Select(), choices=[])

    def __init__(self, data=None,initial=None):
        super(IndicatorFilterForm, self).__init__(data=data, initial=initial)
        all_surveys, all_batches, all_modules = self.set_all_choices(data)
        self.fields['survey'].choices = all_surveys
        self.fields['batch'].choices = all_batches
        self.fields['module'].choices = all_modules

    def set_all_choices(self, data=None):
        all_batches = [('All', 'All')]
        all_surveys = [('All', 'All')]
        all_modules = [('All', 'All')]
        batches = Batch.objects.all()
        if data and data.get('survey', None).isdigit():
            batches = batches.filter(survey__id = int(data.get('survey', None)))
        map(lambda batch: all_batches.append((batch.id, batch.name)), batches)
        map(lambda survey: all_surveys.append((survey.id, survey.name)), Survey.objects.all())
        map(lambda module: all_modules.append((module.id, module.name)), QuestionModule.objects.all())

        return all_surveys, all_batches, all_modules
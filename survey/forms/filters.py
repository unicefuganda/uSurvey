from django import forms
from rapidsms.contrib.locations.models import Location
from survey.models import HouseholdMemberGroup, QuestionModule, Question, Batch, Survey, EnumerationArea
MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE = 1000
DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE =50

class QuestionFilterForm(forms.Form):

    groups = forms.ChoiceField(label='Group', widget=forms.Select(), choices=[])
    modules = forms.ChoiceField(label='Module', widget=forms.Select(), choices=[])
    question_types = forms.ChoiceField(label='Question Type', widget=forms.Select(), choices=[])
    number_of_questions_per_page = forms.IntegerField(max_value=MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE, min_value=20)

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
        self.fields['number_of_questions_per_page'].default = DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE


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
            batches = batches.filter(survey__id=int(data.get('survey', None)))
        map(lambda batch: all_batches.append((batch.id, batch.name)), batches)
        map(lambda survey: all_surveys.append((survey.id, survey.name)), Survey.objects.all())
        map(lambda module: all_modules.append((module.id, module.name)), QuestionModule.objects.all())

        return all_surveys, all_batches, all_modules


class LocationFilterForm(forms.Form):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), empty_label=None)
    batch = forms.ModelChoiceField(queryset=None, empty_label=None)
    location = forms.ModelChoiceField(queryset=Location.objects.all(), widget=forms.HiddenInput(), required=False)
    ea = forms.ModelChoiceField(queryset=None, widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(LocationFilterForm, self).__init__(*args, **kwargs)
        self.constrain_batch_and_ea_choices_to_survey()

    def constrain_batch_and_ea_choices_to_survey(self):
        survey_id = self.data.get('survey', None)
        survey_id = survey_id if str(survey_id).isdigit() else self.fields['survey'].queryset[0].id
        self.fields['batch'].queryset = Batch.objects.filter(survey=survey_id)
        self.fields['ea'].queryset = EnumerationArea.objects.filter(survey=survey_id)


class SurveyBatchFilterForm(forms.Form):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all().order_by('name'), empty_label=None)
    batch = forms.ModelChoiceField(queryset=None, empty_label="All", required=False)

    def __init__(self, *args, **kwargs):
        super(SurveyBatchFilterForm, self).__init__(*args, **kwargs)
        self.constrain_batch_choices_to_survey()

    def constrain_batch_choices_to_survey(self):
        survey_id = self.data.get('survey', None)
        survey_id = survey_id if str(survey_id).isdigit() else self.fields['survey'].queryset[0].id
        self.fields['batch'].queryset = Batch.objects.filter(survey=survey_id).order_by('name')
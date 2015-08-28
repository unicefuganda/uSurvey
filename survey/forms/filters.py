from django import forms
from rapidsms.contrib.locations.models import Location
from survey.models import HouseholdMemberGroup, QuestionModule, Question, Batch, Survey, EnumerationArea, SurveyAllocation
from django.contrib.auth.handlers.modwsgi import groups_for_user
MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE = 1000
DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE =20

class QuestionFilterForm(forms.Form):

    groups = forms.ChoiceField(label='Group', widget=forms.Select(), choices=[], required=False)
    modules = forms.ChoiceField(label='Module', widget=forms.Select(), choices=[])
    question_types = forms.ChoiceField(label='Question Type', widget=forms.Select(), choices=[])

    def __init__(self, data=None,initial=None, read_only=[], batch=None):
        super(QuestionFilterForm, self).__init__(data=data, initial=initial)
        group_choices = [('All', 'All')]
        module_choices = [('All', 'All')]
        question_type_choices = [('All', 'All')]
        map(lambda group: group_choices.append((group.id, group.name)), HouseholdMemberGroup.objects.all().exclude(name='REGISTRATION GROUP'))
        map(lambda question_module: module_choices.append((question_module.id, question_module.name)), QuestionModule.objects.all())
        if batch is None:
            map(lambda question_type: question_type_choices.append(question_type), list(Question.ANSWER_TYPES))
        else:
            map(lambda question_type: question_type_choices.append(question_type), 
                [(name, name) for name in batch.answer_types ])
        self.fields['groups'].choices = group_choices
        self.fields['modules'].choices = module_choices
        self.fields['question_types'].choices = question_type_choices
        for field in read_only:
            self.fields[field].widget.attrs['readonly'] = True
            self.fields[field].widget.attrs['disabled'] = True
        
    def filter(self, questions):
        query_dict = None
        if self.is_valid():
            query_dict = {'group' : self.cleaned_data['groups'], 
                          'module' : self.cleaned_data['modules'],
                        'answer_type': self.cleaned_data['question_types']}
            for key, val in query_dict.items():
                if val == 'All' or not val:
                    del query_dict[key]
        if query_dict is None:
            query_dict = {'group__in' : [key for key, val in  self.fields['groups'].choices if not val == 'All'], 
                      'module__in' : [key for key, val in self.fields['modules'].choices if not val == 'All'],
                    'answer_type__in': [key for key, val in self.fields['question_types'].choices if not val == 'All']}
        return questions.filter(**query_dict)
            

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
        ea = SurveyAllocation.objects.get(survey=survey_id).interviewer.ea
        self.fields['ea'].queryset = EnumerationArea.objects.filter(pk=ea.pk)


class SurveyBatchFilterForm(forms.Form):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all().order_by('name'), empty_label=None)
    batch = forms.ModelChoiceField(queryset=None, empty_label="All", required=False)

    def __init__(self, *args, **kwargs):
        super(SurveyBatchFilterForm, self).__init__(*args, **kwargs)
        self.constrain_batch_choices_to_survey()

    def constrain_batch_choices_to_survey(self):
        survey_id = self.data.get('survey', None)
        batches = Batch.objects.filter(survey__pk=survey_id)
        if batches:
            batches = batches.order_by('name')
        self.fields['batch'].queryset = batches
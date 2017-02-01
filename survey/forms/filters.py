from django import forms
from survey.models import RespondentGroup, QuestionModule, Question, Batch, Survey, EnumerationArea, Location, \
    LocationType
from django.contrib.auth.handlers.modwsgi import groups_for_user
MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE = 1000
DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE = 20


class QuestionFilterForm(forms.Form):
    question_types = forms.ChoiceField(
        label='Answer Type', widget=forms.Select(), choices=[], required=False)

    def __init__(self, data=None, initial=None, read_only=[], qset=None):  # ttype can be batch, listing question, etc
        super(QuestionFilterForm, self).__init__(data=data, initial=initial)
        question_type_choices = [('All', 'All')]
        if qset is None:
            map(lambda question_type: question_type_choices.append(
                question_type), list(Question.ANSWER_TYPES))
        else:
            map(lambda question_type: question_type_choices.append(question_type),
                [(name, name) for name in qset.answer_types])
        self.fields['question_types'].choices = question_type_choices
        for field in read_only:
            self.fields[field].widget.attrs['readonly'] = True
            self.fields[field].widget.attrs['disabled'] = True

    def _query_dict(self, questions):
        query_dict = None
        if self.is_valid():
            query_dict = {'answer_type': self.cleaned_data['question_types']}
            for key, val in query_dict.items():
                if val == 'All' or not val:
                    del query_dict[key]
        if query_dict is None:
            query_dict = {'answer_type__in': [key for key, val in
                                              self.fields['question_types'].choices if not val == 'All']}
        return query_dict

    def filter(self, questions):
        return questions.filter(**self._query_dict(questions))


class BatchQuestionFilterForm(QuestionFilterForm):

    groups = forms.ChoiceField(
        label='Group', widget=forms.Select(), choices=[], required=False)
    modules = forms.ChoiceField(
        label='Module', widget=forms.Select(), choices=[], required=False)

    def __init__(self, data=None, initial=None, read_only=[], batch=None):
        super(BatchQuestionFilterForm, self).__init__(data=data, initial=initial, read_only=read_only, qset=batch)
        group_choices = [('All', 'All')]
        module_choices = [('All', 'All')]
        # map(lambda group: group_choices.append((group.id, group.name)),
        #     HouseholdMemberGroup.objects.all().exclude(name='REGISTRATION GROUP'))
        map(lambda question_module: module_choices.append(
            (question_module.id, question_module.name)), QuestionModule.objects.all())
        self.fields['groups'].choices = group_choices
        self.fields['modules'].choices = module_choices
        for field in read_only:
            self.fields[field].widget.attrs['readonly'] = True
            self.fields[field].widget.attrs['disabled'] = True

    def _query_dict(self, questions):
        query_dict = None
        if self.is_valid():
            query_dict = {'group': self.cleaned_data['groups'],
                          'module': self.cleaned_data['modules'],
                          'answer_type': self.cleaned_data['question_types']}
            for key, val in query_dict.items():
                if val == 'All' or not val:
                    del query_dict[key]
        if query_dict is None:
            query_dict = {'group__in': [key for key, val in self.fields['groups'].choices if not val == 'All'],
                          'module__in': [key for key, val in self.fields['modules'].choices if not val == 'All'],
                          'answer_type__in': [key for key, val in
                                              self.fields['question_types'].choices if not val == 'All']}
        return query_dict


class IndicatorFilterForm(forms.Form):
    survey = forms.ChoiceField(label='Survey', widget=forms.Select(
        attrs={'id': 'id_filter_survey'}), choices=[], required=False)
    batch = forms.ChoiceField(
        label='Batch', widget=forms.Select(), choices=[], required=False)
    module = forms.ChoiceField(
        label='Module', widget=forms.Select(), choices=[], required=False)

    def __init__(self, data=None, initial=None):
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
        map(lambda survey: all_surveys.append(
            (survey.id, survey.name)), Survey.objects.all())
        map(lambda module: all_modules.append(
            (module.id, module.name)), QuestionModule.objects.all())

        return all_surveys, all_batches, all_modules


class LocationFilterForm(forms.Form):
    survey = forms.ModelChoiceField(
        queryset=Survey.objects.all().order_by('name'), empty_label='----')
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.none(), empty_label='----')
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(), widget=forms.HiddenInput(), required=False)
    ea = forms.ModelChoiceField(
        queryset=None, widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(LocationFilterForm, self).__init__(*args, **kwargs)
        if self.data.get('survey'):
            survey = Survey.objects.get(id=self.data['survey'])
            self.fields[
                'batch'].queryset = survey.batches.all().order_by('name')
            self.fields['ea'].queryset = EnumerationArea.objects.filter(
                survey_allocations__survey=survey)


class SurveyBatchFilterForm(forms.Form):
    AS_TEXT = 1
    AS_LABEL = 0
    survey = forms.ModelChoiceField(
        queryset=Survey.objects.all().order_by('name'), empty_label='----')
    batch = forms.ModelChoiceField(queryset=Batch.objects.all(
    ).order_by('name'), empty_label='----', required=False)
    multi_option = forms.ChoiceField(
        choices=[(AS_TEXT, 'As Text'), (AS_LABEL, 'As Value')])

    def __init__(self, *args, **kwargs):
        super(SurveyBatchFilterForm, self).__init__(*args, **kwargs)
        # import  pdb; pdb.set_trace()
        if self.data.get('survey'):
            survey = Survey.objects.get(id=self.data['survey'])
            self.fields['batch'].queryset = survey.batches.all()


class BatchOpenStatusFilterForm(forms.Form):
    OPEN = 1
    CLOSED = 2
    status = forms.ChoiceField(
        label='Status', widget=forms.Select(), choices=[(0, '-- All Status --'), (OPEN, 'Open'),
                                                        (CLOSED, 'Closed')], required=False)

    def __init__(self, batch, *args, **kwargs):
        super(BatchOpenStatusFilterForm, self).__init__(*args, **kwargs)
        self.batch = batch

    def get_locations(self):
        status = None
        try:
            if self.is_valid():
                status = int(self.cleaned_data['status'])
        except forms.ValidationError:
            pass
        prime_location_type = LocationType.largest_unit()
        locations = Location.objects.filter(
            type=prime_location_type).order_by('name')
        batch_location_ids = self.batch.open_locations.values_list('location_id', flat=True)
        if status and status == self.OPEN:
            return locations.filter(id__in=batch_location_ids)
        elif status and status == self.CLOSED:
            return locations.exclude(id__in=batch_location_ids)
        return locations

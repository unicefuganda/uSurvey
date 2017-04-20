from django import forms
from survey.models import RespondentGroup, QuestionModule, Question, Batch, Survey, EnumerationArea, Location, \
    LocationType, Indicator, BatchQuestion, Interview, QuestionSet, ListingTemplate
MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE = 1000
DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE = 20


class QuestionFilterForm(forms.Form):
    question_types = forms.ChoiceField(
        label='Answer Type', widget=forms.Select(), choices=[], required=False)

    # ttype can be batch, listing question, etc
    def __init__(self, data=None, initial=None, read_only=[], qset=None):
        super(QuestionFilterForm, self).__init__(data=data, initial=initial)
        question_type_choices = [('All', 'All')]
        if qset is None:
            map(lambda question_type: question_type_choices.append(
                question_type), list(Question.ANSWER_TYPES))
        else:
            map(lambda question_type: question_type_choices.append(
                question_type), [(name, name) for name in qset.answer_types])
        self.fields['question_types'].choices = question_type_choices
        for field in read_only:
            self.fields[field].widget.attrs['readonly'] = True
            self.fields[field].widget.attrs['disabled'] = True

    def filter(self, questions):
        if self.is_valid() and self.cleaned_data['question_types'] != 'All':
            return questions.filter(
                answer_type=self.cleaned_data['question_types'])
        return questions


class BatchQuestionFilterForm(QuestionFilterForm):

    groups = forms.ChoiceField(
        label='Group', widget=forms.Select(), choices=[], required=False)
    modules = forms.ChoiceField(
        label='Module', widget=forms.Select(), choices=[], required=False)

    def __init__(self, data=None, initial=None, read_only=[], batch=None):
        super(
            BatchQuestionFilterForm,
            self).__init__(
            data=data,
            initial=initial,
            read_only=read_only,
            qset=batch)
        group_choices = [('All', 'All')]
        module_choices = [('All', 'All')]
        # map(lambda group: group_choices.append((group.id, group.name)),
        # HouseholdMemberGroup.objects.all().exclude(name='REGISTRATION
        # GROUP'))
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
            query_dict = {
                'group__in': [
                    key for key,
                    val in self.fields['groups'].choices if not val == 'All'],
                'module__in': [
                    key for key,
                    val in self.fields['modules'].choices if not val == 'All'],
                'answer_type__in': [
                    key for key,
                    val in self.fields['question_types'].choices if not val == 'All']}
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
        queryset=Location.objects.all(),
        widget=forms.HiddenInput(),
        required=False)
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
        queryset=Survey.objects.all().order_by('name'),
        empty_label='Choose Survey',
        widget=forms.Select(
            attrs={
                'class': 'chzn-select'}))
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all().order_by('name'),
        empty_label='Choose Batch',
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'chzn-select'}))
    multi_option = forms.ChoiceField(
        choices=[
            (AS_TEXT, 'As Text'), (AS_LABEL, 'As Value'), ], widget=forms.Select(
            attrs={
                'class': 'chzn-select'}))

    def __init__(self, *args, **kwargs):
        super(SurveyBatchFilterForm, self).__init__(*args, **kwargs)
        if self.data.get('survey'):
            survey = Survey.objects.get(id=self.data['survey'])
            self.fields['batch'].queryset = survey.batches.all()


class BatchOpenStatusFilterForm(forms.Form):
    OPEN = 1
    CLOSED = 2
    status = forms.ChoiceField(label='Status', widget=forms.Select(), choices=[(
        0, '-- All Status --'), (OPEN, 'Open'), (CLOSED, 'Closed')], required=False)

    def __init__(self, batch, *args, **kwargs):
        super(BatchOpenStatusFilterForm, self).__init__(*args, **kwargs)
        self.batch = batch

    def get_locations(self):
        status = None
        try:
            if self.is_valid():
                status = int(self.cleaned_data.get('status') or 0)
        except forms.ValidationError:
            pass
        prime_location_type = LocationType.largest_unit()
        locations = Location.objects.filter(
            type=prime_location_type).order_by('name')
        batch_location_ids = self.batch.open_locations.values_list(
            'location_id', flat=True)
        if status and status == self.OPEN:
            return locations.filter(id__in=batch_location_ids)
        elif status and status == self.CLOSED:
            return locations.exclude(id__in=batch_location_ids)
        return locations


class UsersFilterForm(forms.Form):
    ACTIVE = 1
    DEACTIVATED = 2
    status = forms.ChoiceField(
        label='Status',
        widget=forms.Select(),
        choices=[
            (0,
             '-- All Status --'),
            (ACTIVE,
             'Active'),
            (DEACTIVATED,
             'Deactivated')],
        required=False)

    def get_users(self):
        from django.contrib.auth.models import User
        status = None
        try:
            if self.is_valid():
                status = int(self.cleaned_data.get('status') or 0)
        except forms.ValidationError:
            pass
        if status:
            return User.objects.filter(
                is_active=(
                    status == self.ACTIVE)).exclude(
                is_superuser=True).order_by('first_name')
        return User.objects.exclude(is_superuser=True).order_by('first_name')


class IndicatorMetricFilterForm(forms.Form):
    metric = forms.ChoiceField(
        choices=[
            (Indicator.COUNT,
             'Count'),
            (Indicator.PERCENTAGE,
             'Percentage')],
        initial=Indicator.COUNT)


class MapFilterForm(forms.Form):
    survey = forms.ModelChoiceField(
        queryset=Survey.objects.all(),
        required=False,
        empty_label='Choose Survey',
        widget=forms.Select(
            attrs={
                'class': 'map-filter chzn-select'}),
        label='')


class QuestionSetResultsFilterForm(forms.Form):

    def __init__(self, qset, *args, **kwargs):
        super(QuestionSetResultsFilterForm, self).__init__(*args, **kwargs)
        self.qset = QuestionSet.get(pk=qset.pk)
        if hasattr(self.qset, 'survey') is False:
            self.fields['survey'] = forms.ModelChoiceField(queryset=Survey.objects.filter(
                listing_form__pk=self.qset.pk), required=False, empty_label='Choose Survey')

    def get_interviews(self):
        kwargs = {'question_set': self.qset}
        if self.data.get('survey', None):
            kwargs['survey__id'] = self.data['survey']
        return Interview.objects.filter(**kwargs)


class SurveyResultsFilterForm(forms.Form):
    survey = forms.ModelChoiceField(
        queryset=Survey.objects.all(), required=False)
    question_set = forms.ModelChoiceField(
        queryset=QuestionSet.objects.all(), required=False)

    def __init__(self, model_class, disabled_fields=[], *args, **kwargs):
        super(SurveyResultsFilterForm, self).__init__(*args, **kwargs)
        self.fields['question_set'].label = model_class.verbose_name()
        self.fields['question_set'].widget.attrs['class'] = 'chzn-select'
        self.fields['question_set'].widget.attrs['disabled'] = 'question_set' in disabled_fields
        self.fields['survey'].widget.attrs['class'] = 'chzn-select'
        self.fields['survey'].widget.attrs['disabled'] = 'survey' in disabled_fields
        model_queryset = model_class.objects.all()
        self.fields['question_set'].queryset = model_queryset
        if self.data.get('survey', None) and model_class == ListingTemplate:
            self.fields['question_set'].queryset = model_queryset.filter(
                survey_settings__id=self.data['survey'])
        elif self.data.get('survey', None) and model_class == Batch:
            self.fields['question_set'].queryset = model_queryset.filter(
                survey__id=self.data['survey'])
        elif 'question_set' in disabled_fields and (self.data.get('question_set', None)
                                                    and model_class == ListingTemplate):
            self.fields['survey'].queryset = Survey.objects.filter(
                listing_form__id=self.data['question_set'])

    def get_interviews(self, interviews=Interview.objects):
        kwargs = {}
        if self.data.get('survey', None):
            kwargs['survey__id'] = self.data['survey']
        if self.data.get('question_set', None):
            kwargs['question_set__id'] = self.data['question_set']
        return interviews.filter(**kwargs)

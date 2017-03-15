__author__ = 'anthony'

from django.core.exceptions import ValidationError
from django import forms
from form_helper import FormOrderMixin
from survey.forms.widgets import InlineRadioSelect
from survey.models import Answer, Interview, VideoAnswer, AudioAnswer, ImageAnswer, TextAnswer, NumericalAnswer,\
    MultiChoiceAnswer, MultiSelectAnswer, DateAnswer, SurveyAllocation, EnumerationArea, Survey, QuestionSet, \
    Interviewer, InterviewerAccess, USSDAccess, QuestionOption
from django.conf import settings


class USSDSerializable(object):

    def render_extra_ussd(self):
        pass


def get_answer_form(interview):
    question = interview.last_question
    answer_class = Answer.get_class(question.answer_type)
    access = InterviewerAccess.get(id=interview.interview_channel.id)

    class AnswerForm(forms.ModelForm, USSDSerializable):

        class Meta:
            model = answer_class
            fields = ['value']

        def __init__(self, *args, **kwargs):
            super(AnswerForm, self).__init__(*args, **kwargs)
            self.fields['uid'] = forms.CharField(initial=access.user_identifier,
                                                 widget=forms.HiddenInput)
            if question.answer_type == DateAnswer.choice_name():
                self.fields['value'] = forms.DateField(label='Answer',
                                                       input_formats=[settings.DATE_FORMAT,],
                                                       widget=forms.DateInput(attrs={'placeholder': 'Date Of Birth',
                                                                                     'class': 'datepicker'},
                                                                              format=settings.DATE_FORMAT))
            if question.answer_type == MultiChoiceAnswer.choice_name() and \
                            access.choice_name() == USSDAccess.choice_name():
                self.fields['value'] = forms.IntegerField()
            elif question.answer_type == MultiChoiceAnswer.choice_name():
                self.fields['value'] = forms.ChoiceField(choices=[(opt.order, opt.text) for opt
                                                                  in question.options.all()], widget=forms.RadioSelect)
                self.fields['value'].empty_label = None
            if question.answer_type == MultiSelectAnswer.choice_name():
                self.fields['value'] = forms.ModelMultipleChoiceField(queryset=question.options.all(),
                                                                      widget=forms.CheckboxSelectMultiple)
            accept_types = {
                            AudioAnswer.choice_name(): 'audio/*',
                            VideoAnswer.choice_name(): 'video/*',
                            ImageAnswer.choice_name(): 'image/*'
                            }
            if question.answer_type in [AudioAnswer.choice_name(), VideoAnswer.choice_name(), ImageAnswer.choice_name()]:
                self.fields['value'].widget.attrs = {'accept': accept_types.get(question.answer_type,
                                                                                '|'.join(accept_types.values()))}
            self.fields['value'].label = 'Answer'

        def render_extra_ussd(self):
            text = []
            if question.options.count() > 0:
                map(lambda opt: text.append('%s: %s' % (opt.order, opt.text)), question.options.all())
            return '\n'.join(text)

        def clean_value(self):
            if question.answer_type == MultiChoiceAnswer.choice_name():
                try:
                    self.cleaned_data['value'] = question.options.get(order=self.cleaned_data['value'])
                except QuestionOption.DoesNotExist:
                    raise ValidationError('Please select a valid option')
            return self.cleaned_data['value']

        def save(self, *args, **kwargs):
            return answer_class.create(interview, question, self.cleaned_data['value'])

    return AnswerForm


class BaseSelectInterview(forms.ModelForm):

    def __init__(self, access, *args, **kwargs):
        super(BaseSelectInterview, self).__init__(*args, **kwargs)
        if 'data' in kwargs:
            kwargs['data']._mutable = True
            kwargs['data']['uid'] = access.user_identifier
            kwargs['data']._mutable = False
        self.interviewer = access.interviewer
        self.fields['uid'] = forms.CharField(initial=access.user_identifier, widget=forms.HiddenInput)

    class Meta:
        model = Interview
        fields = []


class SelectInterviewForm(BaseSelectInterview):

    def __init__(self, access, *args, **kwargs):
        super(SelectInterviewForm, self).__init__(access, *args, **kwargs)
        self.fields['survey'].queryset = Survey.objects.filter(pk__in=[sa.survey.pk for sa in
                                                                       self.interviewer.unfinished_assignments])
        self.fields['survey'].empty_label = 'Select Survey'
        self.fields['question_set'].label = 'Batch'
        self.fields['question_set'].queryset = QuestionSet.objects.none()
        self.fields['question_set'].empty_label = 'Select Batch'
        self.fields['ea'].queryset = EnumerationArea.objects.filter(pk__in=[sa.allocation_ea.pk for sa in
                                                                            self.interviewer.unfinished_assignments])
        self.fields['ea'].empty_label = 'Select EA'
        # self.fields['test_data'].initial = True
        # self.fields['ea'].widget.attrs['class']+ = 'chzn-select'
        if self.data.get('survey'):
            self.fields['question_set'].queryset = Survey.objects.get(pk=self.data['survey']).qsets

    class Meta:
        model = Interview
        fields = ['survey', 'question_set', 'ea', 'test_data']


class UserAccessForm(forms.Form):
    uid = forms.CharField(label='Mobile/ODK ID', max_length=25)

    def clean_uid(self):
        try:
            access = InterviewerAccess.get(user_identifier=self.cleaned_data['uid'])
        except InterviewerAccess.DoesNotExist:
            raise ValidationError('No such user')
        return access


class SurveyAllocationForm(BaseSelectInterview, FormOrderMixin):
    ea = forms.ChoiceField(widget=forms.RadioSelect)

    def __init__(self, access, *args, **kwargs):
        super(SurveyAllocationForm, self).__init__(access, *args, **kwargs)
        self.fields['ea'].choices = [(idx+1, sa.allocation_ea.name) for idx, sa in
                                     enumerate(self.interviewer.unfinished_assignments.order_by('allocation_ea__name'))]
        self.order_fields(['ea', 'test_data'])
        # self.fields['ea'].empty_label = 'Select EA'
        #self.fields['ea'].widget = forms.RadioSelect()

    def clean_ea(self):
        selected = int(self.cleaned_data['ea'])
        return self.interviewer.unfinished_assignments.order_by('allocation_ea__name')[selected - 1].allocation_ea

    def selected_allocation(self):
        if self.is_valid():
            selected = int(self.data['ea'])
            return self.interviewer.unfinished_assignments.order_by('allocation_ea__name')[selected - 1]

    def save(self, commit=True):
        instance = super(SurveyAllocationForm, self).save(commit=commit)
        instance.survey = self.selected_allocation().survey
        instance.ea = self.cleaned_data['ea']
        instance.interviewer = self.interviewer
        return instance

    class Meta:
        model = Interview
        fields = ['test_data', ]


class SelectBatchForm(BaseSelectInterview):

    def __init__(self, access, survey, *args, **kwargs):
        super(SelectBatchForm, self).__init__(access, *args, **kwargs)
        self.survey = survey
        self.fields['batch'] = forms.ChoiceField()
        self.fields['batch'].choices = [(idx+1, batch.name) for idx, batch in
                                        enumerate(survey.batches.all().order_by('name'))]

    def clean_batch(self):
        selected = int(self.cleaned_data['batch'])
        return self.survey.batches.all().order_by('name')[selected-1]


class SelectInterviewerForm(forms.Form):
    interviewer = forms.ModelChoiceField(queryset=Interviewer.objects.all())

    class Meta:
        widgets = {
            'interviewer': forms.Select(attrs={'class': 'chzn-select', }),
        }




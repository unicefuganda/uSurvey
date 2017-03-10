__author__ = 'anthony'

from django.core.exceptions import ValidationError
from django import forms
from survey.forms.widgets import InlineRadioSelect
from survey.models import Answer, Interview, VideoAnswer, AudioAnswer, ImageAnswer, TextAnswer, NumericalAnswer,\
    MultiChoiceAnswer, MultiSelectAnswer, DateAnswer, SurveyAllocation, EnumerationArea, Survey, QuestionSet, \
    Interviewer
from django.conf import settings


def get_answer_form(interview):
    question = interview.last_question
    answer_class = Answer.get_class(question.answer_type)

    class AnswerForm(forms.ModelForm):

        class Meta:
            model = answer_class
            fields = ['value']

        def __init__(self, *args, **kwargs):
            super(AnswerForm, self).__init__(*args, **kwargs)
            if question.answer_type == DateAnswer.choice_name():
                self.fields['value'] = forms.DateField(label='Answer',
                                                       input_formats=[settings.DATE_FORMAT,],
                                                       widget=forms.DateInput(attrs={'placeholder': 'Date Of Birth',
                                                                                     'class': 'datepicker'},
                                                           format=settings.DATE_FORMAT))
            if question.answer_type == MultiChoiceAnswer.choice_name():
                self.fields['value'] = forms.ModelChoiceField(queryset=question.options.all())
            if question.answer_type == MultiSelectAnswer.choice_name():
                self.fields['value'] = forms.ModelMultipleChoiceField(queryset=question.options.all(),
                                                                      widget=forms.SelectMultiple(attrs={
                                                                          'class': 'multi-select'}))
            accept_types = {
                            AudioAnswer.choice_name(): 'audio/*',
                            VideoAnswer.choice_name(): 'video/*',
                            ImageAnswer.choice_name(): 'image/*'
                            }
            if question.answer_type in [AudioAnswer.choice_name(), VideoAnswer.choice_name(), ImageAnswer.choice_name()]:
                self.fields['value'].widget.attrs = {'accept': accept_types.get(question.answer_type,
                                                                                '|'.join(accept_types.values()))}
            self.fields['value'].label = 'Answer'

        def save(self, *args, **kwargs):
            return answer_class.create(interview, question, self.cleaned_data['value'])

    return AnswerForm


class SelectInterviewForm(forms.ModelForm):
    #ea = forms.ModelChoiceField(queryset=EnumerationArea.objects.none(), empty_label='Select EA')

    def __init__(self, interviewer, *args, **kwargs):
        super(SelectInterviewForm, self).__init__(*args, **kwargs)
        self.fields['survey'].queryset = Survey.objects.filter(pk__in=[sa.survey.pk for sa in
                                                                       interviewer.unfinished_assignments])
        self.fields['survey'].empty_label = 'Select Survey'
        self.fields['question_set'].queryset = QuestionSet.objects.none()
        self.fields['question_set'].empty_label = 'Select Question Set'
        self.fields['ea'].queryset = EnumerationArea.objects.filter(pk__in=[sa.allocation_ea.pk for sa in
                                                                            interviewer.unfinished_assignments])
        self.fields['ea'].empty_label = 'Select EA'
        # self.fields['ea'].widget.attrs['class'] = 'chzn-select'
        if self.data.get('survey'):
            self.fields['question_set'].queryset = Survey.objects.get(pk=self.data['survey']).qsets

    class Meta:
        model = Interview
        fields = ['survey', 'question_set', 'ea' ]



class SelectInterviewerForm(forms.Form):
    interviewer = forms.ModelChoiceField(queryset=Interviewer.objects.all())

    class Meta:
        widgets = {
            'interviewer': forms.Select(attrs={'class': 'chzn-select', }),
        }



# class LooptypeForm(forms.Form)
#     'has_sampling': InlineRadioSelect(choices=((True, 'Sampled'), (False, 'Census')),



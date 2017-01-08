from collections import OrderedDict
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django import forms
from form_order_mixin import FormOrderMixin
from survey.models import Answer, MultiChoiceAnswer, MultiSelectAnswer, DateAnswer, QuestionFlow, \
    Question, TextArgument, NumericalAnswer, TextAnswer, TemplateOption
from survey.models import QuestionLoop, FixedLoopCount, PreviousAnswerCount
from survey.models.helper_constants import CONDITIONS



class LogicForm(forms.Form):
    SKIP_TO = 'SKIP_TO'
    END_INTERVIEW = 'END_INTERVIEW'
    REANSWER = 'REANSWER'
    ASK_SUBQUESTION = 'ASK_SUBQUESTION'
    BACK_TO = 'BACK_TO'
    BACK_TO_ACTION = 'BACK TO'
    SUBQUESTION_ACTION = 'ASK SUBQUESTION'
    ACTIONS = {
        END_INTERVIEW: 'END INTERVIEW',
        SKIP_TO: 'SKIP TO',
        REANSWER: 'RECONFIRM',
        # BACK_TO: BACK_TO_ACTION,
        ASK_SUBQUESTION: SUBQUESTION_ACTION,
    }

    def __init__(self, question, initial=None, *args, **kwargs):
        super(LogicForm, self).__init__(initial=initial, *args, **kwargs)
        data = kwargs.get('data', None)
        batch = question.qset
        self.question = question
        self.batch = batch
        self.fields['condition'] = forms.ChoiceField(label='Eligibility criteria', choices=[], widget=forms.Select,
                                                     required=False)
        self.fields['attribute'] = forms.ChoiceField(label='Attribute', choices=[('value', 'Value'), ],
                                                     widget=forms.Select, required=False)
        self.fields['condition'].choices = [(validator.__name__, validator.__name__.upper())
                                            for validator in Answer.get_class(question.answer_type).validators()]
        if question.answer_type in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer.choice_name()]:
            self.fields['option'] = forms.ChoiceField(
                label='', choices=[], widget=forms.Select, required=True)
            self.fields['option'].choices = [
                (option.order, option.text) for option in question.options.all()]
        else:
            self.fields['value'] = forms.CharField(label='', required=False)
            self.fields['min_value'] = forms.CharField(label='', required=False,
                                                       widget=forms.TextInput(attrs={'placeholder': 'Min Value'}))
            self.fields['max_value'] = forms.CharField(label='', required=False,
                                                       widget=forms.TextInput(attrs={'placeholder': 'Max Value'}))
            if question.answer_type == DateAnswer.choice_name():
                self.fields['value'].widget.attrs['class'] = 'datepicker'
                self.fields['min_value'].widget.attrs['class'] = 'datepicker'
                self.fields['max_value'].widget.attrs['class'] = 'datepicker'
            # validate_with_question = forms.ChoiceField(label='', choices=[], widget=forms.Select, required=False)
        self.fields['action'] = forms.ChoiceField(
            label='Then', choices=[], widget=forms.Select, required=True)
        flows = self.question.flows.all()
        existing_nexts = [f.next_question.pk for f in flows if f.next_question]
        next_q_choices = [(q.pk, q.text) for q in batch.questions_inline(
        ) if q.pk is not self.question.pk]
        # and q.pk not in existing_nexts]
        next_q_choices.extend([(q.pk, q.text)
                               for q in batch.zombie_questions()])
        self.fields['next_question'] = forms.ChoiceField(label='', choices=next_q_choices, widget=forms.Select,
                                                         required=False)
        #self.fields['next_question'].widget.attrs['class'] = 'chzn-select'
        self.fields['action'].choices = self.ACTIONS.items()

        action_sent = data.get('action', None) if data else None

    def clean_value(self):

        if self.question.answer_type not in  [MultiSelectAnswer.choice_name(), MultiChoiceAnswer.choice_name()] \
                and self.cleaned_data['condition'] != 'between' and \
                len(self.cleaned_data['value'].strip()) == 0:
            raise ValidationError("Field is required.")
        value = self.cleaned_data.get('value', '')
        if value:
            Answer.get_class(
                self.question.answer_type).validate_test_value(value)
        return self.cleaned_data.get('value', '')

    def clean_min_value(self):
        if (self.cleaned_data['condition'] == 'between') and len(self.cleaned_data['min_value'].strip()) == 0:
            raise ValidationError("Field is required.")
        value = self.cleaned_data.get('min_value', '')
        if value:
            Answer.get_class(
                self.question.answer_type).validate_test_value(value)
        return self.cleaned_data.get('min_value', '')

    def clean_max_value(self):
        if (self.cleaned_data['condition'] == 'between') and len(self.cleaned_data['max_value'].strip()) == 0:
            raise ValidationError("Field is required.")
        value = self.cleaned_data.get('max_value')
        if value:
            Answer.get_class(
                self.question.answer_type).validate_test_value(value)
        return self.cleaned_data.get('max_value', '')

    def _make_desc(self):
        # return '%s-%s' % (self.cleaned_data['condition'],
        # self.ACTIONS[self.cleaned_data['action']])
        return self.ACTIONS[self.cleaned_data['action']]

    def clean_next_question(self):
        if self.cleaned_data['action'] in [self.ASK_SUBQUESTION, self.SKIP_TO, self.BACK_TO]:
            try:
                int(self.cleaned_data.get('next_question', ''))
            except:
                raise ValidationError('Next question is required for Skip or Sub questions')
        return self.cleaned_data.get('next_question', '')

    def clean(self):
        field_name = ""
        rule = []
        desc = self._make_desc()
        flows = QuestionFlow.objects.filter(question=self.question)

        if len(flows) > 0:
            for flow in flows:
                if self.cleaned_data['condition'] == 'between':
                    min_val = self.cleaned_data.get('min_value')
                    max_val = self.cleaned_data.get('max_value')
                    min_arg = flow.text_arguments.filter(
                        position=0, param=min_val).exists()
                    max_arg = flow.text_arguments.filter(
                        position=0, param=max_val).exists()
                    if max_arg and min_arg:
                        raise ValidationError("This rule already exists.")
                elif flow.text_arguments.filter(position=0, param=self.cleaned_data.get('value', '').strip()).exists():
                    raise ValidationError("This rule already exists.")
                if flow.next_question and flow.next_question.pk == self.cleaned_data.get('next_question', ''):
                    raise ValidationError(
                        "Logic rule already exists to selected next question.")

        return self.cleaned_data

    def save(self, *args, **kwargs):
        next_question = None
        desc = self._make_desc()
        if self.cleaned_data['action'] in [self.ASK_SUBQUESTION, self.SKIP_TO, self.BACK_TO]:
            next_question = Question.get(pk=self.cleaned_data['next_question'])
        if self.cleaned_data['action'] == self.REANSWER:
            next_question = self.question
        flow = QuestionFlow.objects.create(question=self.question,
                                           validation_test=self.cleaned_data[
                                               'condition'],
                                           next_question=next_question,
                                           desc=desc)
        if self.cleaned_data['action'] == self.ASK_SUBQUESTION:
            # connect back to next inline question of the main
            QuestionFlow.objects.create(question=next_question,
                                        desc=desc,
                                        next_question=self.batch.next_inline(self.question))
        if self.cleaned_data['condition'] == 'between':
            TextArgument.objects.create(
                flow=flow, position=0, param=self.cleaned_data['min_value'])
            TextArgument.objects.create(
                flow=flow, position=1, param=self.cleaned_data['max_value'])
        else:
            value = self.cleaned_data.get('value', '')
            if self.question.answer_type in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer.choice_name()]:
                value = self.cleaned_data['option']
            TextArgument.objects.create(flow=flow, position=0, param=value)
        # clean up now, remove all zombie questions
        self.question.qset.zombie_questions().delete()


class LoopingForm(forms.ModelForm, FormOrderMixin):
    FIXED_COUNT = FixedLoopCount.choice_name()
    PREVIOUS_ANSWER_COUNT = PreviousAnswerCount.choice_name()
    repeat_count = forms.IntegerField(required=False)

    def __init__(self, loop_starter, initial=None, *args, **kwargs):
        super(LoopingForm, self).__init__(initial=initial, *args, **kwargs)
        self.fields['loop_starter'].widget = forms.HiddenInput()
        self.fields['loop_starter'].initial = loop_starter.pk
        self.fields['loop_ender'].label = 'Loop Ends At:'
        self.fields['loop_ender'].queryset = Question.objects.filter(pk__in=[q.pk for
                                                                             q in loop_starter.upcoming_inlines()])
        self.fields['previous_numeric_values'] = forms.ModelChoiceField(queryset=Question.objects.filter(
            pk__in=[q.pk for q in loop_starter.previous_inlines() if q.answer_type == NumericalAnswer.choice_name()]
        ))
        self.fields['previous_numeric_values'].empty_label = 'Code - Question'
        if self.instance:
            prev_question_count = getattr(self.instance, PreviousAnswerCount.choice_name(), None)
            fixed_count = getattr(self.instance, FixedLoopCount.choice_name(), None)
            if prev_question_count:
                self.fields['previous_numeric_values'].initial = prev_question_count.value.pk
            if fixed_count:
                self.fields['repeat_count'].initial = fixed_count.value
        # self.fields['previous_numeric_values'].widget = forms.
        # self.fields['repeat_count'].widget = forms.TextInput(attrs={'disabled': 'disabled'})
        self.fields['previous_numeric_values'].required = False
        self.order_fields(['loop_starter', 'loop_label', 'repeat_logic', 'previous_numeric_values',
                                'repeat_count', 'loop_ender'])

    class Meta:
        model = QuestionLoop
        exclude = []

    def clean(self):
        super(LoopingForm, self).clean()
        repeat_logic = self.cleaned_data.get('repeat_logic', '')
        if repeat_logic == self.FIXED_COUNT:
            try:
                int(self.cleaned_data.get('repeat_count', ''))
            except ValueError:
                raise ValidationError('repeat count is required')
        if repeat_logic == self.PREVIOUS_ANSWER_COUNT and not self.cleaned_data.get(
                'previous_numeric_values', False):
            raise ValidationError('No previous answer selected')
        # check for overlapping loops between start and end
        # start_question = self.cleaned_data['loop_starter']
        # end_question = self.cleaned_data['loop_ender']
        # QuestionFlow.objects.filter(Q(question__in=start_question.qset.inlines_between(start_question, end_question))|
        #                             Q(next_question__in=start_question.qset.inlines_between(start_question,
        #                                                                                     end_question)),
        #                             desc__in=[LogicForm.SKIP_TO, LogicForm.END_INTERVIEW]).exist():

        return self.cleaned_data

    def save(self, commit=True, *args, **kwargs):
        loop = super(LoopingForm, self).save(commit, *args, **kwargs)
        if commit:
            prev_question_count = getattr(self.instance, PreviousAnswerCount.choice_name(), None)
            fixed_count = getattr(self.instance, FixedLoopCount.choice_name(), None)
            if prev_question_count:
                prev_question_count.delete()
            if fixed_count:
                fixed_count.delete()
            if loop.repeat_logic == self.FIXED_COUNT:
                FixedLoopCount.objects.create(loop=loop, value=self.cleaned_data['repeat_count'])
            elif loop.repeat_logic == self.PREVIOUS_ANSWER_COUNT:
                PreviousAnswerCount.objects.create(loop=loop, value=self.cleaned_data['previous_numeric_values'])
        return loop



from django import forms
from cacheops import cached_as
from django import template
from django.forms import ModelForm
from survey.models import Indicator, Batch, QuestionModule, Survey, QuestionOption, IndicatorVariableCriteria, \
    IndicatorVariable
from survey.models import BatchQuestion, Question, Answer, MultiChoiceAnswer, MultiSelectAnswer, NumericalAnswer
from django.core.exceptions import ValidationError
from survey.forms.form_order_mixin import FormOrderMixin


class IndicatorForm(ModelForm, FormOrderMixin):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), empty_label=None)
    batch = forms.ModelChoiceField(queryset=Batch.objects.none(), empty_label='Select Batch', required=False)

    def __init__(self, *args, **kwargs):
        super(IndicatorForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            batch = kwargs['instance'].parameter.qset
            batch = Batch.get(pk=batch.pk)
            survey = batch.survey
            self.fields['survey'].initial = survey
            self.fields['batch'].queryset = survey.batches
            self.fields['batch'].initial = batch
        if self.data.get('survey'):
            self.fields['batch'].queryset = Batch.objects.filter(
                survey=self.data['survey'])
        self.fields['name'].label = 'Indicator'
        self.order_fields(['name', 'description', 'survey', 'batch', ])

    def clean(self):
        super(IndicatorForm, self).clean()
        batch = self.cleaned_data.get('batch', None)
        survey = self.cleaned_data.get('survey', None)
        if batch and batch.survey != survey:
            message = "Batch %s does not belong to the selected Survey." % (
                batch.name)
            self._errors['batch'] = self.error_class([message])
            del self.cleaned_data['batch']
        return self.cleaned_data

    class Meta:
        model = Indicator
        exclude = []


class IndicatorVariableForm(ModelForm, FormOrderMixin):
    min = forms.IntegerField(required=False)
    max = forms.IntegerField(required=False)
    value = forms.CharField(required=False)
    options = forms.ChoiceField(choices=[], required=False)
    CHOICES = [('', '--------------------')]
    CHOICES.extend(IndicatorVariableCriteria.VALIDATION_TESTS)
    validation_test = forms.ChoiceField(choices=CHOICES, required=False,
                                        label='Operator')
    test_question = forms.ModelChoiceField(queryset=Question.objects.none(), required=False)

    def __init__(self, indicator, *args, **kwargs):
        super(IndicatorVariableForm, self).__init__(*args, **kwargs)
        self.indicator = indicator
        self.order_fields(['name', 'description', 'test_question', 'validation_test', 'options', 'value',
                           'min', 'max'])
        self.fields['test_question'].queryset = Question.objects.filter(pk__in=[q.pk
                                                                                for q in
                                                                                indicator.batch.all_questions
                                                                                ])
        if self.data.get('test_question', []):
            options = QuestionOption.objects.filter(question__pk=self.data['test_question'])
            self.fields['options'].choices = [(opt.order, opt.text) for opt in options]

    class Meta:
        model = IndicatorVariable
        exclude = ['indicator', ]
        widgets = {'description': forms.Textarea(attrs={"rows": 2, "cols": 100}), }

    def clean_name(self):
        self.cleaned_data['name'] = self.cleaned_data['name'].replace(' ', '_')
        return self.cleaned_data['name']

    def clean(self):
        validation_test = self.cleaned_data.get('validation_test', None)
        test_question = self.cleaned_data.get('test_question', None)
        if validation_test is None or test_question is None:
            return self.cleaned_data
        answer_class = Answer.get_class(test_question.answer_type)
        method = getattr(answer_class, validation_test, None)
        if method is None:
            raise forms.ValidationError('unsupported validator defined on test question')
        if validation_test == 'between':
            if self.cleaned_data.get('min', False) is False or self.cleaned_data.get('max', False) is False:
                raise forms.ValidationError('min and max values required for between condition')
        elif self.cleaned_data.get('value', False) is False:
            raise forms.ValidationError('Value is required for %s' % validation_test)
        if test_question.answer_type in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer]:
            if self.cleaned_data.get('options', False) is False:
                raise forms.ValidationError('No option selected for %s' % test_question.identifier)
            self.cleaned_data['value'] = self.cleaned_data['options']
        return self.cleaned_data

    def save(self, *args, **kwargs):
        variable = super(IndicatorVariableForm, self).save(commit=False)
        variable.indicator = self.indicator
        variable.save()
        validation_test = self.cleaned_data.get('validation_test', None)
        test_question = self.cleaned_data.get('test_question', None)
        if validation_test and test_question:
            criteria = IndicatorVariableCriteria.objects.create(test_question=test_question, variable=variable,
                                                                validation_test=validation_test)
            if validation_test == 'between':
                criteria.arguments.create(position=0, param=self.cleaned_data['min'])
                criteria.arguments.create(position=1, param=self.cleaned_data['max'])
            else:
                criteria.arguments.create(position=0, param=self.cleaned_data['value'])
        return variable


class IndicatorFormulaeForm(forms.ModelForm):

    class Meta:
        model = Indicator
        include = ['formulae', ]

    def clean_formulae(self):
        pass

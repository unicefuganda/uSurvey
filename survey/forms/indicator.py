from survey.forms.form_order_mixin import FormOrderMixin
from django import forms
from django.forms import ModelForm
from survey.models import Indicator, Batch, QuestionModule, Survey, QuestionOption, IndicatorCriteria
from survey.models import BatchQuestion, Question, Answer, MultiChoiceAnswer, MultiSelectAnswer, NumericalAnswer
from django.core.exceptions import ValidationError
from survey.forms.form_order_mixin import FormOrderMixin


class IndicatorForm(ModelForm, FormOrderMixin):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), empty_label=None)
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.none(), empty_label='Select Batch', required=False)

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
        self.fields['parameter'].queryset = BatchQuestion.objects.filter(answer_type__in=
                                                                         [MultiChoiceAnswer.choice_name(),
                                                                          # NumericalAnswer.choice_name()
                                                                          # shall support only multichoice for now
                                                                          ])
        self.order_fields(['name', 'description', 'survey', 'batch', 'parameter'])

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


class IndicatorCriteriaForm(ModelForm, FormOrderMixin):
    min = forms.IntegerField(required=False)
    max = forms.IntegerField(required=False)
    value = forms.CharField(required=False)
    options = forms.ChoiceField(choices=[], required=False)
    CHOICES = [('', '--------------------')]
    CHOICES.extend(IndicatorCriteria.VALIDATION_TESTS)
    validation_test = forms.ChoiceField(choices=CHOICES, required=False,
                                        label='Operator')

    def __init__(self, indicator, *args, **kwargs):
        super(IndicatorCriteriaForm, self).__init__(*args, **kwargs)
        self.indicator = indicator
        self.order_fields(['name', 'description', 'test_question', 'validation_test', 'options', 'value',
                           'min', 'max'])
        self.fields['test_question'].queryset = Question.objects.filter(pk__in=[q.pk
                                                                                for q in
                                                                                indicator.parameter.e_qset.all_questions
                                                                                ])
        if self.data.get('test_question', []):
            options = QuestionOption.objects.filter(question__pk=self.data['test_question'])
            self.fields['options'].choices = [(opt.order, opt.text) for opt in options]

    class Meta:
        model = IndicatorCriteria
        exclude = ['indicator', ]
        widgets = {
        'description': forms.Textarea(attrs={"rows": 3, "cols": 30}),
        }

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
        criteria = super(IndicatorCriteriaForm, self).save(commit=False)
        criteria.indicator = self.indicator
        criteria.save()
        validation_test = self.cleaned_data.get('validation_test', None)
        if validation_test == 'between':
            criteria.arguments.create(position=0, param=self.cleaned_data['min'])
            criteria.arguments.create(position=1, param=self.cleaned_data['max'])
        else:
            criteria.arguments.create(position=0, param=self.cleaned_data['value'])
        return criteria

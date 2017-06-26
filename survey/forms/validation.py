#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
from django import forms
from survey.forms.form_helper import FormOrderMixin
from survey.models import MultiChoiceAnswer
from survey.models import RespondentGroupCondition
from survey.models import TemplateOption
from survey.models import Answer
from survey.models import RespondentGroup
from survey.models import MultiSelectAnswer
from survey.models import ParameterTemplate


def get_response_validation_form(test_question_model):
    class ValidationForm(forms.ModelForm, FormOrderMixin):
        min = forms.IntegerField(required=False)
        max = forms.IntegerField(required=False)
        value = forms.CharField(required=False)
        options = forms.ChoiceField(choices=[], required=False)
        CHOICES = [('', '----------Create Operator----------')]
        CHOICES.extend(RespondentGroupCondition.VALIDATION_TESTS)
        validation_test = forms.ChoiceField(choices=CHOICES, required=False,
                                            label='Operator')
        test_question = forms.ModelChoiceField(queryset=test_question_model.objects.all(), required=False,
                                               label='Parameter')

        def __init__(self, *args, **kwargs):
            super(ValidationForm, self).__init__(*args, **kwargs)
            self.order_fields(['name',
                               'description',
                               'test_question',
                               'validation_test',
                               'options',
                               'value',
                               'min',
                               'max'])
            if self.data.get('test_question', []):
                options = TemplateOption.objects.filter(
                    question__pk=self.data['test_question'])
                self.fields['options'].choices = [
                    (opt.order, opt.text) for opt in options]

        def clean(self):
            validation_test = self.cleaned_data.get('validation_test', None)
            test_question = self.cleaned_data.get('test_question', None)
            if validation_test is None or test_question is None:
                return self.cleaned_data
            answer_class = Answer.get_class(test_question.answer_type)
            method = getattr(answer_class, validation_test, None)
            if method is None:
                raise forms.ValidationError(
                    'unsupported validator defined on test question')
            if validation_test == 'between':
                if self.cleaned_data.get(
                        'min', False) is False or self.cleaned_data.get(
                        'max', False) is False:
                    raise forms.ValidationError(
                        'min and max values required for between condition')
            elif self.cleaned_data.get('value', False) is False:
                raise forms.ValidationError(
                    'Value is required for %s' %
                    validation_test)
            if test_question.answer_type in [
                    MultiChoiceAnswer.choice_name(),
                    MultiSelectAnswer]:
                if self.cleaned_data.get('options', False) is False:
                    raise forms.ValidationError(
                        'No option selected for %s' %
                        test_question.identifier)
                self.cleaned_data['value'] = self.cleaned_data['options']
            return self.cleaned_data

        def save(self, *args, **kwargs):
            pass

    return ValidationForm

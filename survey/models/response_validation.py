#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
"""This module is designed to provide validation feature in general.
Presently implemented for QuestionFlows but have to expand in general for response validation feature in other models
"""
from django.utils.safestring import mark_safe
from django.db import models
from django_cloneable import CloneableMixin
from survey.models.base import BaseModel
from model_utils.managers import InheritanceManager
from survey.models.interviews import Answer, MultiChoiceAnswer


class ResponseValidation(CloneableMixin, BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    validation_test = models.CharField(max_length=200, choices=VALIDATION_TESTS)
    # if validation passes, classify this flow response as having this value
    constraint_message = models.TextField(default='', blank=True, null=True)

    @property
    def dconstraint_message(self):
        if self.constraint_message:
            return self.constraint_message
        else:
            return unicode(self)

    class Meta:
        app_label = 'survey'

    @property
    def test_params(self):
        return [t.param for t in self.text_arguments]

    @property
    def text_arguments(self):
        return TextArgument.objects.filter(validation=self).order_by('position')

    @property
    def test_arguments(self):
        return TextArgument.objects.filter(validation=self).order_by('position')

    def __unicode__(self):
        return '%s: %s' % (self.validation_test, ', '.join(self.text_arguments.values_list('param', flat=True)))

    def get_odk_constraint(self, test_question):
        answer_class = Answer.get_class(test_question.answer_type)
        return mark_safe(answer_class.print_odk_validation('.', self.validation_test,  *self.test_params))

    def validate(self, value, test_question):
        answer_class = Answer.get_class(test_question.answer_type)
        method = getattr(answer_class, self.validation_test, None)
        return method(value, *self.test_params)


class TestArgument(CloneableMixin, BaseModel):
    object = InheritanceManager()
    validation = models.ForeignKey(ResponseValidation, related_name='%(class)ss', null=True)
    position = models.PositiveIntegerField()

    @classmethod
    def argument_types(cls):
        return [cl.__name__ for cl in cls.__subclasses__()]

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'


class TextArgument(TestArgument):
    param = models.TextField()

    class Meta:
        app_label = 'survey'


class NumberArgument(TestArgument):
    param = models.IntegerField()

    class Meta:
        app_label = 'survey'


class DateArgument(TestArgument):
    param = models.DateField()

    class Meta:
        app_label = 'survey'


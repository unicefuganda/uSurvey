__author__ = 'anthony <>'

from django.db import models
from survey.models.base import BaseModel
from survey.models.interviews import Answer, MultiChoiceAnswer, MultiSelectAnswer


class GenericQuestion(BaseModel):
    ANSWER_TYPES = [(name, name) for name in Answer.answer_types()]
    identifier = models.CharField(
        max_length=100, blank=False, null=True, verbose_name='Variable Name')
    text = models.CharField(max_length=150, blank=False, null=False,)
    answer_type = models.CharField(
        max_length=100, blank=False, null=False, choices=ANSWER_TYPES)

    @classmethod
    def type_name(cls):
        return cls._meta.verbose_name.title()

    class Meta:
        abstract = True


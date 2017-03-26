__author__ = 'anthony <>'
from django.db import models
from survey.models.questions import Question
from survey.models.respondents import RespondentGroup


class BatchQuestion(Question):
    group = models.ForeignKey(RespondentGroup, related_name='questions', null=True, blank=True,
                              on_delete=models.SET_NULL)
    module = models.ForeignKey(
        "QuestionModule", related_name="questions", default='', on_delete=models.SET_NULL, null=True, blank=True)


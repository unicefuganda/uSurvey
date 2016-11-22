__author__ = 'anthony <>'
from django.db import models
from survey.models.questions import Question
from survey.models.respondents import RespondentGroup
from survey.models.access_channels import USSDAccess
from survey.models.base import BaseModel


class BatchQuestion(Question):
    group = models.ForeignKey(RespondentGroup, related_name='questions', null=True, blank=True)
    module = models.ForeignKey(
        "QuestionModule", related_name="questions", default='')


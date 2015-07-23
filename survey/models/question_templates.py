import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from survey.models.interviewer import Interviewer
from survey.models.interviews import Answer
from survey.models.base import BaseModel
from survey.models.access_channels import InterviewerAccess
from model_utils.managers import InheritanceManager


class QuestionTemplate(BaseModel):
    ANSWER_TYPES = [(name, name) for name in Answer.answer_types()]
    identifier = models.CharField(max_length=100, blank=False, null=True, unique=True)
    group = models.ForeignKey("HouseholdMemberGroup", null=True, related_name="question_templates")
    text = models.CharField(max_length=150, blank=False, null=False)
    answer_type = models.CharField(max_length=100, blank=False, null=False, choices=ANSWER_TYPES)
    module = models.ForeignKey("QuestionModule", null=True, related_name="question_templates")

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return "%s - %s: (%s)" % (self.identifier, self.text, self.answer_type.upper())
    
# class QuestionTemplateChannel(BaseModel):
#     ACCESS_CHANNELS = [(name, name) for name in InterviewerAccess.access_channels()]
#     question_template = models.ForeignKey(QuestionTemplate, related_name='access_channels')
#     channel = models.CharField(max_length=100, choices=ACCESS_CHANNELS)
#     
#     class Meta:
#         app_label = 'survey'
#         unique_together = ('question_template', 'channel')


from django.db import models

from survey.models.base import BaseModel
from survey.models.question import Question


class Survey(BaseModel):
    name = models.CharField(max_length=100, blank=False,null=True)
    description = models.CharField(max_length=300,blank=True,null=True)
    questions = models.ManyToManyField(Question, related_name="survey")

    class Meta:
        app_label = 'survey'

from survey.models.base import BaseModel
from django.db import models
from survey.models.question_module import QuestionModule


class Indicator(BaseModel):
    MEASURE_CHOICES = (('%', 'Percentage'),
                       ('Number', 'Number'))
    module = models.ForeignKey(QuestionModule, null=False, related_name='indicator')
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(null=True)
    measure = models.CharField(max_length=255, null=False, choices=MEASURE_CHOICES, default=MEASURE_CHOICES[0][1])
    batch = models.ForeignKey("Batch", null=True)
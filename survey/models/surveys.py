from django.db import models

from survey.models.base import BaseModel

class Survey(BaseModel):
    name = models.CharField(max_length=100, blank=False,null=True)
    description = models.CharField(max_length=300,blank=True,null=True)
    sample_size = models.PositiveIntegerField(max_length=2, null=False, blank=False, default=10)
    type = models.BooleanField(default=False)

    class Meta:
        app_label = 'survey'

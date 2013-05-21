from django.db import models
from django_extensions.db.models import TimeStampedModel

class Investigator(TimeStampedModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    mobile_number = models.CharField(max_length=20, unique=True, null=False, blank=False)

    class Meta:
        app_label = 'survey'
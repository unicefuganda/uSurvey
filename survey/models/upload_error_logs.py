from survey.models import BaseModel
from django.db import models


class UploadErrorLog(BaseModel):
    model = models.CharField(max_length=20, blank=False, null=True)
    filename = models.CharField(max_length=20, blank=True, null=True)
    row_number = models.PositiveIntegerField(blank=True, null=True)
    error = models.CharField(max_length=200, blank=False, null=True)
from django.db import models
from survey.models.base import BaseModel


class AboutUs(BaseModel):
    content = models.TextField(null=False, blank=False)

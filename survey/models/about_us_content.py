from django.db import models
from survey.models.base import BaseModel


class AboutUs(BaseModel):
    content = models.TextField(null=False, blank=False)

class SuccessStories(BaseModel):
	name = models.CharField(max_length=20)
	content = models.TextField(null=False, blank=False)

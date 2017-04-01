from django.db import models
from survey.models.base import BaseModel
import os
import random


class AboutUs(BaseModel):
    content = models.TextField(null=False, blank=False)

def content_file_name(instance, filename):

	filename = filename.replace(' ','_')
	filename = "%s_%s"%(random.randint(1,100),filename)
	return os.path.join('media/success-stories',filename)

class SuccessStories(BaseModel):
	name = models.CharField(max_length=20)
	content = models.TextField(null=False, blank=False)
	image = models.FileField(upload_to=content_file_name)

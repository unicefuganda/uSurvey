import datetime
from django.conf import settings
from django.db import models
from survey.models.base import BaseModel
from survey.models.interviewer import Interviewer
from model_utils.managers import InheritanceManager


class InterviewerAccess(BaseModel):
    DAYS = 'D'
    HOURS = 'H'
    MINUTES = 'M'
    SECONDS = 'S'
    REPONSE_TIMEOUT_DURATIONS = [(DAYS, 'Days'), (HOURS, 'Hours'), (MINUTES, 'Minutes'), (SECONDS, 'Seconds')]
    interviewer = models.ForeignKey(Interviewer)
    user_identifier = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    reponse_timeout = models.PositiveIntegerField(help_text='Max time to wait for response before ending interview')
    duration = models.CharField(choices=REPONSE_TIMEOUT_DURATIONS, max_length=100)
    
    class Meta:
        app_label = 'survey'
     
    @classmethod    
    def access_channels(cls):
        return [cl._meta.verbose_name.title() for cl in cls.__subclasses__()]

class USSDAccess(InterviewerAccess):
    aggregator = models.CharField(choices=settings.AGGREGATORS, max_length=100)
    
    class Meta:
        app_label = 'survey'
    
    def supported_answers(self):
        return 
    
class ODKAccess(InterviewerAccess):
    odk_token = models.CharField(max_length=10, default="12345")
    
    class Meta:
        app_label = 'survey'
    

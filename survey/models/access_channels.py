from django.conf import settings
from django.db import models
from survey.models.base import BaseModel
from model_utils.managers import InheritanceManager
from django.utils.safestring import mark_safe

DEFAULT_TOKEN = getattr(settings, 'DEFAULT_TOKEN', "12345")


class InterviewerAccess(BaseModel):
    DAYS = 'D'
    HOURS = 'H'
    MINUTES = 'M'
    SECONDS = 'S'
    objects = InheritanceManager()
    REPONSE_TIMEOUT_DURATIONS = [
        (DAYS, 'Days'), (HOURS, 'Hours'), (MINUTES, 'Minutes'), (SECONDS, 'Seconds')]
    interviewer = models.ForeignKey('Interviewer', related_name='%(class)s')
    user_identifier = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, verbose_name='Activated')
    reponse_timeout = models.PositiveIntegerField(default=1000,
                                                  help_text='Max time to wait for response before ending interview',
                                                  null=True, blank=True)
    duration = models.CharField(default=HOURS, choices=REPONSE_TIMEOUT_DURATIONS, max_length=100,
                                null=True, blank=True)

    class Meta:
        app_label = 'survey'

    @classmethod
    def choice_name(cls):
        return cls._meta.verbose_name.title()

    @classmethod
    def access_channels(cls):
        return [cl.choice_name() for cl in cls.__subclasses__()]

    def __unicode__(self):
        name = '<span style="color: %s;">%s</span>' % (
            'green' if self.is_active else 'red', self.user_identifier)
        return mark_safe(name)


class USSDAccess(InterviewerAccess):
    aggregator = models.CharField(choices=settings.AGGREGATORS, max_length=100, null=True, blank=True,
                                  default=settings.DEFAULT_AGGREGATOR)

    class Meta:
        app_label = 'survey'


class ODKAccess(InterviewerAccess):
    odk_token = models.CharField(max_length=10, default=DEFAULT_TOKEN)

    class Meta:
        app_label = 'survey'


class WebAccess(InterviewerAccess):
    pass

    class Meta:
        app_label = 'survey'

from django.db import models


class Backend(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return self.name
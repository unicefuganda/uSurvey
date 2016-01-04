from django_extensions.db.models import TimeStampedModel

class BaseModel(TimeStampedModel):
    class Meta:
        app_label = 'survey'
        abstract = True

    # def __int__(self):
    #     return self.pk
from django_extensions.db.models import TimeStampedModel


class BaseModel(TimeStampedModel):

    class Meta:
        app_label = 'survey'
        abstract = True

    def __repr__(self):
        if hasattr(self, 'id'):
            return '%s-%s' % (self.__class__.__name__, self.id)
        else:
            return super(BaseModel, self).__repr__()

    # def __int__(self):
    #     return self.pk

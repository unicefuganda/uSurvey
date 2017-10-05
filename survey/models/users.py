from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from django.conf import settings
from survey.models.base import BaseModel


class UserProfile(BaseModel):
    user = models.OneToOneField(User, related_name="userprofile")
    mobile_number = models.CharField(
        validators=[
            MinLengthValidator(settings.MOBILE_NUM_MIN_LENGTH),
            MaxLengthValidator(settings.MOBILE_NUM_MAX_LENGTH)],
        max_length=settings.MOBILE_NUM_MAX_LENGTH,
        unique=True,
        null=False,
        blank=False)

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return '%s<%s>' % (self.user.first_name, self.user.email)

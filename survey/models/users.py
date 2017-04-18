from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from survey.models.base import BaseModel


class UserProfile(BaseModel):
    user = models.OneToOneField(User, related_name="userprofile")
    mobile_number = models.CharField(
        validators=[
            MinLengthValidator(9),
            MaxLengthValidator(9)],
        max_length=10,
        unique=True,
        null=False,
        blank=False)

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return '"%s"<%s>' % (self.user.first_name, self.user.email)

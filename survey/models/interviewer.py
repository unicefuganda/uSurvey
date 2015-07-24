import datetime
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from survey.investigator_configs import LEVEL_OF_EDUCATION, LANGUAGES, COUNTRY_PHONE_CODE
from survey.models.base import BaseModel


class Interviewer(BaseModel):
    MALE = 1
    FEMALE = 0
    name = models.CharField(max_length=100, blank=False, null=False)
    gender = models.CharField(default=MALE, verbose_name="Sex", choices=[(MALE, "M"), (FEMALE, "F")], max_length=10)
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(50)], null=True)
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    is_blocked = models.BooleanField(default=False)
    ea = models.ForeignKey("EnumerationArea", null=True, related_name="interviewers")
    language = models.CharField(max_length=100, null=True, choices=LANGUAGES,
                                blank=False, default='English', verbose_name="Preferred language of communication")
    weights = models.FloatField(default=0, blank=False)
    

    class Meta:
        app_label = 'survey'


import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from survey.interviewer_configs import LEVEL_OF_EDUCATION, MONTHS
from survey.models.base import BaseModel
from survey.models.interviewer import Interviewer
from survey.models.surveys import Survey
from survey.models.interviews import Answer
from survey.models.access_channels import InterviewerAccess
from django.core.exceptions import ValidationError


class Household(BaseModel):
    REGISTRATION_CHANNELS = [(name, name) for name in InterviewerAccess.access_channels()]
    ea = models.ForeignKey("EnumerationArea", null=True, related_name="household_enumeration_area")
#     uid = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="Interviewer Unique Identification for the Household")
    house_number = models.PositiveIntegerField(verbose_name="Household Number in EA")
    household_code = models.CharField(max_length=100, null=True, verbose_name="Household Code")
    registrar = models.ForeignKey(Interviewer, related_name='registered_households')
    survey = models.ForeignKey(Survey, related_name='registered_households')
    registration_channel = models.CharField(max_length=100, choices=REGISTRATION_CHANNELS)
    
    class Meta:
        app_label = 'survey'
        unique_together = [('survey', 'house_number'), ]
    
    def __unicode__(self):
        return 'HH-%s-%s' % (self.house_number, self.head.surname)
    
    def clean(self):
        super(Household, self).clean()
        if self.house_number > self.total_households:
             raise ValidationError('Household number has exceeded total households in the Enumeration area')
    
    @property
    def head(self):
        return HouseholdHead.objects.get(household=self)

    def _get_related_location_name(self, key, location_hierarchy):
        location_object = location_hierarchy.get(key, None)
        location_name = ""
        if location_object:
            location_name = location_object.name
        return location_name

    def get_related_location(self):
        location_hierarchy = self.location_hierarchy()
        related_location = SortedDict()
        return related_location
    
    @classmethod
    def set_related_locations(cls, households):
        for household in households:
            household.related_locations = household.get_related_location()
        return households

class HouseholdMember(BaseModel):
    MALE = 1
    FEMALE = 0
    surname = models.CharField(max_length=25, verbose_name="Family Name")
    first_name = models.CharField(max_length=25, blank=True, null=True, verbose_name="Other Names")
    gender = models.BooleanField(default=True, verbose_name="Sex", choices=[(MALE, 'M'), (FEMALE, 'F')])
    date_of_birth = models.DateField(auto_now=False)
    household = models.ForeignKey(Household, related_name='household_member')
#     registrar = models.ForeignKey(Interviewer, related_name='registered_household_members')
#     registration_channel = models.ForeignKey(InterviewerAccess, related_name='registered_household_members')

    def __unicode__(self):
        return '%s, %s' % (self.surname, self.first_name)

    def answers(self, batch):
        answers = []
        map(lambda answer_class: 
            answers.extend(answer_class.objects.filter(householdmember=self, batch=batch)), 
            Answer.answer_types)
        return answers

    class Meta:
        app_label = 'survey'
        get_latest_by = 'created'


class HouseholdHead(HouseholdMember):
    occupation = models.CharField(max_length=100, blank=False, null=False,
                                  verbose_name="Occupation / Main Livelihood", default="16")
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    resident_since = models.DateField(auto_now=False) #typically only month and year would be filled
#     resident_since_year = models.PositiveIntegerField(validators=[MinValueValidator(1930), MaxValueValidator(2100)],
#                                                       null=False, default=1984)
#     resident_since_month = models.PositiveIntegerField(null=False, choices=MONTHS, blank=False, default=5)

    class Meta:
        app_label = 'survey'

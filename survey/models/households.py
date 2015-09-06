from datetime import date, datetime
from django.utils.datastructures import SortedDict
import dateutils
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from survey.interviewer_configs import LEVEL_OF_EDUCATION, MONTHS
from survey.models.base import BaseModel
from survey.models.interviews import Answer
from survey.models.access_channels import InterviewerAccess
from survey.models.householdgroups import HouseholdMemberGroup
from survey.models.household_batch_completion import HouseSurveyCompletion, HouseholdBatchCompletion, \
            HouseholdMemberBatchCompletion, HouseMemberSurveyCompletion
from django.core.exceptions import ValidationError


class Household(BaseModel):
    REGISTRATION_CHANNELS = [(name, name) for name in InterviewerAccess.access_channels()]
    ea = models.ForeignKey("EnumerationArea", null=True, related_name="household_enumeration_area")
#     uid = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="Interviewer Unique Identification for the Household")
    house_number = models.PositiveIntegerField(verbose_name="Household Number")
    household_code = models.CharField(max_length=100, null=True, verbose_name="Household Code")
    registrar = models.ForeignKey('Interviewer', related_name='registered_households', verbose_name='Interviewer')
    survey = models.ForeignKey('Survey', related_name='registered_households')
    registration_channel = models.CharField(max_length=100, choices=REGISTRATION_CHANNELS)
    
    class Meta:
        app_label = 'survey'
        unique_together = [('survey', 'house_number', 'ea'), ]
    
    def __unicode__(self):
        return 'HH-%s' % self.house_number
    
    # def clean(self):
    #     super(Household, self).clean()
    #     if self.house_number > self.ea.total_households:
    #          raise ValidationError('Household number has exceeded total households in the Enumeration area')
    
    def get_head(self):
        try:
            return HouseholdHead.objects.get(household=self)
        except HouseholdHead.DoesNotExist:
            return None
    
    @property
    def members(self):
        return HouseholdMember.objects.filter(household=self)

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
    
    @classmethod
    def all_households_in(cls, location, survey, ea=None):
        all_households = Household.objects.filter(survey=survey)
        if ea:
            return all_households.filter(ea=ea)
        return all_households.filter(ea__locations__in=location.get_descendants(include_self=True))

    def has_completed(self):
        completion_recs = HouseMemberSurveyCompletion.objects.filter(householdmember__household=self, survey=self.survey).distinct()
        return completion_recs.count() == self.members.count()

    def has_completed_batch(self, batch):
        completion_recs = HouseholdMemberBatchCompletion.objects.filter(householdmember__household=self, batch=batch).distinct()
        return completion_recs.count() == self.members.count()

    def survey_completed(self):
        return HouseSurveyCompletion.objects.create(household=self, survey=self.survey, interviewer=self.registrar)

    def batch_completed(self, batch):
        return HouseholdBatchCompletion.objects.create(household=self, batch=batch, interviewer=self.registrar)


class HouseholdMember(BaseModel):
    MALE = 1
    FEMALE = 0
    surname = models.CharField(max_length=25, verbose_name="Family Name")
    first_name = models.CharField(max_length=25, blank=True, null=True, verbose_name="Other Names")
    gender = models.BooleanField(default=True, verbose_name="Sex", choices=[(MALE, 'M'), (FEMALE, 'F')])
    date_of_birth = models.DateField(auto_now=False)
    household = models.ForeignKey(Household, related_name='household_members')
#     registrar = models.ForeignKey(Interviewer, related_name='registered_household_members')
#     registration_channel = models.ForeignKey(InterviewerAccess, related_name='registered_household_members')

    def is_head(self):
        return False

    def __unicode__(self):
        return '%s, %s' % (self.surname, self.first_name)

    def answers(self, batch):
        answers = []
        map(lambda answer_class: 
            answers.extend(answer_class.objects.filter(householdmember=self, batch=batch)), 
            Answer.answer_types)
        return answers
    
    @property
    def age(self):
        return dateutils.relativedelta(datetime.utcnow().date(), self.date_of_birth).years
    
    def belongs_to(self, member_group):
        attributes = {'AGE': self.age,
                      'GENDER': self.gender,
                      'GENERAL': self.is_head()
                      }
        for condition in member_group.get_all_conditions():
            if not condition.matches(attributes):
                return False
        return True

    @property
    def groups(self):
        groups = HouseholdMemberGroup.objects.all()
        groups = filter(lambda group: self.belongs_to(group), groups)
        return groups

    def batch_completed(self, batch):
        return HouseholdMemberBatchCompletion.objects.create(householdmember=self,
                                                              batch=batch,
                                                              interviewer=self.household.registrar)

    def survey_completed(self):
        return HouseMemberSurveyCompletion.objects.create(householdmember=self,
                                                           interviewer=self.household.registrar,
                                                           survey=self.household.survey)

    class Meta:
        app_label = 'survey'
        get_latest_by = 'created'


class HouseholdHead(HouseholdMember):
    occupation = models.CharField(max_length=100, blank=False, null=False,
                                  verbose_name="Occupation / Main Livelihood", default="16")
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    resident_since = models.DateField(auto_now=False, verbose_name='Since when have you lived here') #typically only month and year would be filled

    def is_head(self):
        return False

    class Meta:
        app_label = 'survey'

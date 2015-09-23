from datetime import date, timedelta, datetime
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from survey.interviewer_configs import LEVEL_OF_EDUCATION, LANGUAGES, COUNTRY_PHONE_CODE, INTERVIEWER_MIN_AGE, INTERVIEWER_MAX_AGE
from survey.models.base import BaseModel
from survey.models.access_channels import USSDAccess, ODKAccess, InterviewerAccess
from survey.models.locations import Location
import random
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from survey.models.household_batch_completion import HouseSurveyCompletion, HouseholdBatchCompletion
from survey.models.households import Household, SurveyHouseholdListing, HouseholdListing, RandomSelection
from rapidsms.router import send

def validate_min_date_of_birth(value):
    if relativedelta(datetime.utcnow().date(), value).years < INTERVIEWER_MIN_AGE:
        raise ValidationError('interviewers must be at most %s years' % INTERVIEWER_MIN_AGE)

def validate_max_date_of_birth(value):
    if relativedelta(datetime.utcnow().date(), value).years > INTERVIEWER_MAX_AGE:
        raise ValidationError('interviewers must not be at more than %s years' % INTERVIEWER_MAX_AGE)

class Interviewer(BaseModel):
    MALE = '1'
    FEMALE = '0'
    name = models.CharField(max_length=100, blank=False, null=False)
    gender = models.CharField(default=MALE, verbose_name="Sex", choices=[(MALE, "M"), (FEMALE, "F")], max_length=10)
#     age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(50)], null=True)
    date_of_birth = models.DateField(null=True, validators=[validate_min_date_of_birth, validate_max_date_of_birth])
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    is_blocked = models.BooleanField(default=False)
    ea = models.ForeignKey('EnumerationArea', null=True, related_name="interviewers", verbose_name='Enumeration Area')
    language = models.CharField(max_length=100, null=True, choices=LANGUAGES,
                                blank=False, default='English', verbose_name="Preferred language of communication")
    weights = models.FloatField(default=0, blank=False)

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return self.name

    @property
    def age(self):
        return relativedelta(datetime.utcnow().date(), self.date_of_birth).years

    def total_households_completed(self, survey=None):
        try:
            if survey is None:
                survey = self.assignments.get(completed=False).survey
            return HouseSurveyCompletion.objects.filter(survey=survey, interviewer=self).distinct().count()
        except:
            return 0

    def total_households_batch_completed(self, batch):
        return HouseholdBatchCompletion.objects.filter(batch=batch, interviewer=self).distinct().count()


    def completed_batch_or_survey(self, survey, batch):
        if survey and not batch:
            return self.total_households_completed(survey) > 0
        return self.total_households_batch_completed(batch) > 0

    def locations_in_hierarchy(self):
        locs = self.ea.locations.all() #this should evaluate to country
        if locs:
            return locs[0].get_ancestors(include_self=True)
        else:
            Location.objects.none()

    @property
    def ussd_access(self):
        return USSDAccess.objects.filter(interviewer=self)

    @property
    def access_ids(self):
        accesses = self.intervieweraccess.all()
        ids = []
        if accesses.exists():
            ids = [acc.user_identifier for acc in accesses]
        return ids

    @property
    def odk_access(self):
        return ODKAccess.objects.filter(interviewer=self)
    
    def get_ussd_access(self, mobile_number):
        return USSDAccess.objects.get(interviewer=self, user_identifier=mobile_number)

    def get_odk_access(self, identifier):
        return ODKAccess.objects.get(interviewer=self, user_identifier=identifier)
    
    def present_households(self, survey=None):
        if survey is None:
            return Household.objects.filter(listing__ea=self.ea)
        else:
            # import pdb; pdb.set_trace()
            # listings = HouseholdListing.objects.filter(survey_houselistings__survey=survey, ea=self.ea)
            return Household.objects.filter(listing__ea=self.ea, listing__survey_houselistings__survey=survey)
    
    def generate_survey_households(self, survey):
        survey_households = self.present_households(survey)
        if survey.has_sampling:
            selections = RandomSelection.objects.filter(survey=survey, household__listing__ea=self.ea).distinct()
            households = [s.household for s in selections]
            if survey.sample_size > selections.count():
                #random select households as per sample size
                #first shuffle registered households and select up to sample number
                sample_size = survey.sample_size - selections.count()
                if households:
                    survey_households = survey_households.exclude(pk__in=households)
                ###to do bulk create
                survey_households = list(survey_households)
                random.shuffle(survey_households)
                survey_households = survey_households[:sample_size]
                random_selections = []
                for household in survey_households:
                    random_selections.append(RandomSelection(household=household, survey=survey))
                RandomSelection.objects.bulk_create(random_selections)
            else:
                survey_households = households
        return sorted(survey_households, key=lambda household: household.house_number)

    def has_survey(self):
        return self.assignments.filter(completed=False).count() > 0

    @property
    def has_access(self):
        return self.intervieweraccess.objects.filter(is_active=True).exists()

    @classmethod
    def sms_interviewers_in_locations(cls, locations, text):
        interviewers = []
        for location in locations:
            interviewers.extend(Interviewer.objects.filter(ea__locations__in=location.get_leafnodes(True)))
        # send(text, interviewers)

    def allocated_surveys(self):
        return self.assignments.filter(completed=False, allocation_ea=self.ea)

class SurveyAllocation(BaseModel):
    interviewer = models.ForeignKey(Interviewer, related_name='assignments')
    survey = models.ForeignKey('Survey', related_name='work_allocation')
    allocation_ea = models.ForeignKey('EnumerationArea', related_name='survey_allocations')
    completed = models.BooleanField(default=False)

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return self.survey.name
    
    @classmethod
    def get_allocation(cls, interviewer):
        try:
            allocation = cls.get_allocation_details(interviewer)
            if allocation:
                return allocation.survey
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_allocation_details(cls, interviewer):
        try:
            return cls.objects.get(interviewer=interviewer, allocation_ea=interviewer.ea, completed=False)
        except cls.DoesNotExist:
            return None

    def batches_enabled(self):
        return self.survey.batches_enabled(ea=self.allocation_ea)
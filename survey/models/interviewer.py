from datetime import date, timedelta, datetime
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from survey.interviewer_configs import LEVEL_OF_EDUCATION, LANGUAGES, INTERVIEWER_MIN_AGE, INTERVIEWER_MAX_AGE
from survey.models.base import BaseModel
from survey.models.access_channels import USSDAccess, ODKAccess, InterviewerAccess
from survey.models.locations import Location
import random
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from survey.models.household_batch_completion import HouseSurveyCompletion, HouseholdBatchCompletion
from survey.models.households import Household, SurveyHouseholdListing, HouseholdListing, RandomSelection
from survey.utils.sms import send_sms


def validate_min_date_of_birth(value):
    if relativedelta(datetime.utcnow().date(), value).years < INTERVIEWER_MIN_AGE:
        raise ValidationError(
            'interviewers must be at most %s years' % INTERVIEWER_MIN_AGE)


def validate_max_date_of_birth(value):
    if relativedelta(datetime.utcnow().date(), value).years > INTERVIEWER_MAX_AGE:
        raise ValidationError(
            'interviewers must not be at more than %s years' % INTERVIEWER_MAX_AGE)


class Interviewer(BaseModel):
    MALE = '1'
    FEMALE = '0'
    name = models.CharField(max_length=100, blank=False, null=False)
    gender = models.CharField(default=MALE, verbose_name="Sex", choices=[
                              (MALE, "M"), (FEMALE, "F")], max_length=10)
#     age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(50)], null=True)
    date_of_birth = models.DateField(
        null=True, validators=[validate_min_date_of_birth, validate_max_date_of_birth])
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    is_blocked = models.BooleanField(default=False)
    ea = models.ForeignKey('EnumerationArea', null=True,        # shall use this to track the interviewer present ea
                           related_name="interviewers", verbose_name='Enumeration Area', blank=True)  # reporting mostly
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
                survey = self.assignments.get(
                    status=SurveyAllocation.PENDING).survey
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
        locs = self.ea.locations.all()  # this should evaluate to country
        if locs:
            return locs[0].get_ancestors(include_self=True).exclude(parent__isnull=True)
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

    # def present_households(self, survey=None):
    #     if survey is None:
    #         return Household.objects.filter(listing__ea=self.ea)
    #     else:
    #         return Household.objects.filter(listing__ea=self.ea, listing__survey_houselistings__survey=survey)
    #
    # def generate_survey_households(self, survey):
    #     survey_households = self.present_households(survey)
    #     if survey.has_sampling:
    #         selections = RandomSelection.objects.filter(
    #             survey=survey, household__listing__ea=self.ea).distinct()
    #         households = [s.household for s in selections]
    #         if survey.sample_size > selections.count():
    #             # random select households as per sample size
    #             # first shuffle registered households and select up to sample
    #             # number
    #             sample_size = survey.sample_size - selections.count()
    #             if households:
    #                 survey_households = survey_households.exclude(
    #                     pk__in=[h.pk for h in households])
    #             # to do bulk create
    #             survey_households = list(survey_households)
    #             random.shuffle(survey_households)
    #             survey_households = survey_households[:sample_size]
    #             random_selections = []
    #             for household in survey_households:
    #                 random_selections.append(RandomSelection(
    #                     household=household, survey=survey))
    #             RandomSelection.objects.bulk_create(random_selections)
    #             survey_households.extend(households)
    #         else:
    #             # import pdb; pdb.set_trace()
    #             survey_households = households
    #         msg = '\n'.join(['Survey: %s' % survey, 'Households: %s' %
    #                          ','.join([str(h) for h in survey_households])])
    #         for access in self.ussd_access:
    #             send_sms(access.user_identifier, msg)
    #     else:
    #         survey_households = list(survey_households)
    #     return sorted(survey_households, key=lambda household: household.house_number)
    #
    # def survey_households(self, survey):
    #     if survey.has_sampling:
    #         selections = RandomSelection.objects.filter(
    #             survey=survey, household__listing__ea=self.ea).distinct()
    #         households = [s.household for s in selections]
    #     else:
    #         households = self.present_households(survey)
    #     return sorted(households, key=lambda household: household.house_number)

    def has_survey(self):
        return self.assignments.filter(status=SurveyAllocation.PENDING).count() > 0

    @property
    def has_access(self):
        return self.intervieweraccess.filter(is_active=True).exists()

    @classmethod
    def sms_interviewers_in_locations(cls, locations, text):
        interviewers = []
        for location in locations:
            interviewers.extend(Interviewer.objects.filter(
                ea__locations__in=location.get_leafnodes(True)))
        # send(text, interviewers)

    def allocated_surveys(self):
        return self.assignments.filter(status=SurveyAllocation.PENDING, allocation_ea=self.ea)


class SurveyAllocation(BaseModel):
    LISTING = 1
    SURVEY = 2
    PENDING = 0
    COMPLETED = 1
    DEALLOCATED = 2
    interviewer = models.ForeignKey(Interviewer, related_name='assignments')
    survey = models.ForeignKey('Survey', related_name='work_allocation')
    allocation_ea = models.ForeignKey(
        'EnumerationArea', related_name='survey_allocations')
    stage = models.CharField(max_length=20, choices=[(LISTING, 'LISTING'),
                                                     (SURVEY, 'SURVEY'), ],
                             null=True, blank=True)
    status = models.IntegerField(default=PENDING, choices=[(PENDING, 'PENDING'), (DEALLOCATED, 'DEALLOCATED'),
                                                           (COMPLETED, 'COMPLETED')])

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return self.survey.name

    @classmethod
    def get_allocation(cls, interviewer, count=0):
        """
        This function is just retained for compatibility sake. Shall be removed in time. Be wary about using it
        :param interviewer:
        :param count:
        :return:
        """
        try:
            allocation = cls.get_allocation_details(interviewer)
            if allocation:
                return allocation[count].survey
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_allocation_details(cls, interviewer):
        try:
            return cls.objects.filter(interviewer=interviewer,
                                      status=cls.PENDING).order_by('created')
        except cls.DoesNotExist:
            return None

    def min_eas_is_covered(self, loc):
        pass

    @classmethod
    def can_start_batch(cls, interviewer):
        survey_allocations = interviewer.assignments.all()
        completed = filter(lambda allocation: allocation.sample_size_reached(), survey_allocations)
        return (1.0 * len(completed))/len(survey_allocations) >= getattr(settings, 'EAS_PERCENT_TO_START_SURVEY', 0.5)

    def is_valid(self):
        '''
        It's up to users of this class to ensure that interviewer as not been assigned to new ea from allocated one
        :return:
        '''
        return self.status == self.PENDING and self.interviewer.ea == self.allocation_ea

    def sample_size_reached(self):
        from survey.models import Interview
        return Interview.objects.filter(interviewer=self.interviewer, survey=self.survey,
                                        ea=self.allocation_ea).count() >= self.survey.sample_size

    def batches_enabled(self):
        if self.is_valid():
            if self.survey.has_sampling:
                if self.interviewer.present_households(self.survey).count() < self.survey.sample_size:
                    return False
            return True
        else:
            raise ValidationError(
                'Interviewer not assigned to EA: ' % self.allocation_ea)

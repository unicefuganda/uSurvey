from datetime import date, datetime
from django.utils.datastructures import SortedDict
import dateutils
import string
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
from django import template
from django.db.models import Max


class HouseholdListing(BaseModel):
    ea = models.ForeignKey("EnumerationArea", null=True,
                           related_name="household_enumeration_area")
    list_registrar = models.ForeignKey(
        'Interviewer', related_name='listings', verbose_name='Interviewer')
    initial_survey = models.ForeignKey('Survey', related_name='listings')
    # total_households = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return '%s-%s' % (self.ea, self.initial_survey)

    class Meta:
        app_label = 'survey'
        unique_together = [('initial_survey', 'ea'), ]


class SurveyHouseholdListing(BaseModel):
    listing = models.ForeignKey(
        HouseholdListing, related_name='survey_houselistings')
    survey = models.ForeignKey('Survey', related_name='survey_house_listings')

    class Meta:
        app_label = 'survey'

    @classmethod
    def get_or_create_survey_listing(cls, interviewer, survey):
        survey_listing = None
        try:
            return cls.objects.get(survey=survey, listing__ea=interviewer.ea)
        except cls.DoesNotExist:
            try:
                listing = HouseholdListing.objects.get(
                    ea=interviewer.ea, initial_survey=survey.preferred_listing)
            except HouseholdListing.DoesNotExist:
                listing = HouseholdListing.objects.create(
                    ea=interviewer.ea, initial_survey=survey, list_registrar=interviewer)
            survey_listing = cls.objects.create(survey=survey, listing=listing)
        return survey_listing


class Household(BaseModel):
    MALE = True
    FEMALE = False
    REGISTRATION_CHANNELS = [(name, name)
                             for name in InterviewerAccess.access_channels()]
    house_number = models.PositiveIntegerField(verbose_name="Household Number")
    listing = models.ForeignKey(HouseholdListing, related_name='households')
    physical_address = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Structure Address")
    last_registrar = models.ForeignKey(
        'Interviewer', related_name='registered_households', verbose_name='Interviewer')
    registration_channel = models.CharField(
        max_length=100, choices=REGISTRATION_CHANNELS)
    head_desc = models.CharField(max_length=200)
    head_sex = models.BooleanField(default=FEMALE)

    class Meta:
        app_label = 'survey'
        unique_together = [('house_number', 'listing'), ]

    def __unicode__(self):
        return 'HH-%s' % self.house_number

    @classmethod
    def next_new_house(cls, listing):
        max = cls.objects.filter(
            listing=listing).aggregate(Max('house_number'))
        if not max:
            max = {'house_number': 0}
        return max['house_number'] + 1

    # def clean(self):
    #     super(Household, self).clean()
    #     if self.house_number > self.ea.total_households:
    #          raise ValidationError('Household number has exceeded total households in the Enumeration area')

    def get_head(self):
        try:
            return HouseholdHead.objects.filter(household=self)[0]
        except IndexError:
            return None

    @property
    def head_name(self):
        head = self.get_head()
        if head:
            return '%s %s' % (head.first_name or '', head.surname or '')

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
        all_households = Household.objects.filter(listing__survey_houselistings__survey=survey,
                                                  listing__ea__locations__in=location.get_leafnodes(include_self=True)).distinct()
        if ea:
            return all_households.filter(listing__ea=ea)
        return all_households

    def has_completed(self, survey):
        completion_recs = HouseMemberSurveyCompletion.objects.filter(
            householdmember__household=self, survey=survey).distinct()
        return completion_recs.count() >= self.members.count()

    def has_completed_batch(self, batch):
        completion_recs = HouseholdMemberBatchCompletion.objects.filter(
            householdmember__household=self, batch=batch).distinct()
        return completion_recs.count() >= self.members.count()

    def survey_completed(self, survey, registrar):
        return HouseSurveyCompletion.objects.create(household=self, survey=survey, interviewer=registrar)

    def batch_completed(self, batch, registrar):
        return HouseholdBatchCompletion.objects.create(household=self, batch=batch, interviewer=registrar)

    def date_interviewed_for(self, batch):
        hmcs = HouseholdMemberBatchCompletion.objects.filter(
            householdmember__household=self, batch=batch)
        if hmcs.exists():
            return hmcs[0].created

    def total_members_interviewed(self, batch):
        return HouseholdMemberBatchCompletion.objects.\
            filter(householdmember__household=self, batch=batch).values(
                'householdmember').distinct().count()


class HouseholdMember(BaseModel):
    MALE = 1
    FEMALE = 0
    surname = models.CharField(max_length=25, verbose_name="Family Name")
    first_name = models.CharField(
        max_length=25, blank=True, null=True, verbose_name="First Name")
    gender = models.BooleanField(default=True, verbose_name="Sex", choices=[
                                 (MALE, 'M'), (FEMALE, 'F')])
    date_of_birth = models.DateField(auto_now=False)
    household = models.ForeignKey(Household, related_name='household_members')
    survey_listing = models.ForeignKey(
        SurveyHouseholdListing, related_name='house_members')
    registrar = models.ForeignKey(
        'Interviewer', related_name='registered_household_members')
    registration_channel = models.CharField(
        max_length=100, choices=Household.REGISTRATION_CHANNELS)

    def is_head(self):
        try:
            HouseholdHead.objects.get(pk=self)
            return True
        except HouseholdHead.DoesNotExist:
            return False

    @property
    def ea(self):
        return self.household.listing.ea

    def __unicode__(self):
        return '%s, %s' % (self.surname, self.first_name)

    def answers(self, batch):
        answers = []
        map(lambda answer_class:
            answers.extend(answer_class.objects.filter(
                householdmember=self, batch=batch)),
            Answer.answer_types)
        return answers

    @property
    def age(self):
        return dateutils.relativedelta(datetime.utcnow().date(), self.date_of_birth).years

    def belongs_to(self, member_group):
        attributes = {'AGE': self.age,
                      'GENDER': str(int(self.gender)),
                      'GENERAL': str(int(self.is_head()))
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
                                                             interviewer=self.registrar)

    def survey_completed(self):
        return HouseMemberSurveyCompletion.objects.create(householdmember=self,
                                                          interviewer=self.registrar,
                                                          survey=self.survey_listing.survey)

    def get_composed(self, raw_text):
        question_context = template.Context(dict([(field.verbose_name.upper().replace(' ', '_'),
                                                   getattr(self, field.name))
                                                  for field in self._meta.fields if hasattr(self, field.name)]))
        return template.Template(raw_text).render(question_context)

    def reply(self, question):
        if self.belongs_to(question.group):
            answer_class = Answer.get_class(question.answer_type)
            answers = answer_class.objects.filter(
                interview__householdmember=self, question=question)
            if answers.exists():
                reply = unicode(answers[0].to_text())
                return string.capwords(reply)
        return ''

    class Meta:
        app_label = 'survey'
        get_latest_by = 'created'


class HouseholdHead(HouseholdMember):
    occupation = models.CharField(max_length=100, blank=False, null=False,
                                  verbose_name="Occupation / Main Livelihood", default="16")
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    resident_since = models.DateField(auto_now=False, verbose_name='Since when have you lived here', null=True,
                                      blank=True)  # typically only month and year would be filled

    def is_head(self):
        return True

    def save(self, *args, **kwargs):
        if HouseholdHead.objects.filter(household=self.household,
                                        survey_listing=self.survey_listing).exclude(pk=self.pk).exists():
            raise ValidationError('Head already exists')
        else:
            return super(HouseholdHead, self).save(*args, **kwargs)

    class Meta:
        app_label = 'survey'
        verbose_name = 'Main Respondent'


class RandomSelection(BaseModel):
    survey = models.ForeignKey('Survey', related_name='random_selections')
    household = models.OneToOneField(
        Household, related_name='random_selection')

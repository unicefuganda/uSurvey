from django.db import models
from django_cloneable import CloneableMixin
from survey.models.base import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator
from survey.models.locations import Location, LocationType


class Survey(CloneableMixin, BaseModel):
    name = models.CharField(max_length=100, blank=False,
                            null=True, unique=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    has_sampling = models.BooleanField(
        default=True, verbose_name='Survey Type')
    # next three are only relevant for listing data. I believe it saves unnecessary extra tables to refer to them here
    sample_size = models.PositiveIntegerField(null=False, blank=False, default=10)
    listing_form = models.ForeignKey('ListingTemplate', related_name='survey_settings', null=True)
    preferred_listing = models.ForeignKey('Survey', related_name='listing_users',
                                          help_text='Select which survey listing to reuse. '
                                                    'Leave empty for fresh listing',
                                          null=True, blank=True)
    random_sample_label = models.TextField(null=True, blank=True, verbose_name='Randomly selected data label')
    # random_sample_description = models.TextField()


    class Meta:
        app_label = 'survey'
        ordering = ['name', ]
        permissions = (
            ("view_completed_survey", "Can view Completed interviewers"),
        )

    def __unicode__(self):
        return self.name

    @classmethod
    def save_sample_size(cls, survey_form):
        survey = survey_form.save(commit=False)
        if not survey.has_sampling:
            survey.sample_size = 0
        survey.save()

    def is_open_for(self, location):
        all_batches = self.batches.all()
        for batch in all_batches:
            if batch.is_open_for(location):
                return True
        return False

    def eas_covered(self):
        return self.interviews.distinct('ea').count()

    def is_open(self):
        return any([batch.is_open() for batch in self.batches.all()])

    def generate_completion_report(self, batch=None):
        from survey.models.interviewer import Interviewer
        data = []
        all_interviewers = Interviewer.objects.all()
        for interviewer in all_interviewers:
            if interviewer.completed_batch_or_survey(self, batch=batch):
                row = [interviewer.name, ','.join(interviewer.access_ids)]
                if interviewer.ea:
                    row.extend(interviewer.locations_in_hierarchy(
                    ).values_list('name', flat=True))
                data.append(row)
        return data

    @property
    def registered_households(self):
        from survey.models.households import Household
        return Household.objects.filter(listing__survey_houselistings__survey=self).distinct()
    # def batches_enabled(self, interviewer):
    #     if self.has_sampling:
    #         if interviewer.present_households(self).count() < self.sample_size:
    #             return False
    #     return True

    def bulk_enable_batches(self, eas):
        register = []
        for ea in eas:
            register.append(BatchCommencement(survey=self, ea=ea))
        BatchCommencement.objects.bulk_create(register)

    def bulk_disable_batches(self, eas):
        return self.commencement_registry.filter(ea__in=eas).delete()

    def enable_batches(self, ea):
        return BatchCommencement.objects.create(survey=self, ea=ea)

    def disable_batches(self, ea):
        return self.commencement_registry.filter(ea=ea).delete()

    def deep_clone(self):
        from survey.models import Batch
        from survey.models import Question, QuestionFlow
        # first clone this survey
        survey = self.clone(attrs={'name': '%s-copy' % self.name})
        # not create survey batches for this one
        for batch in Batch.objects.filter(survey__id=self.id):
            batch.deep_clone(survey=survey)
        return survey


class SurveySampleSizeReached(Exception):
    pass


class BatchCommencement(BaseModel):
    survey = models.ForeignKey(
        Survey, null=True, related_name='commencement_registry')
    ea = models.ForeignKey('EnumerationArea', null=True,
                           related_name='commencement_registry')

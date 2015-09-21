from django.db import models
from survey.models.base import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator
from survey.models.locations import Location, LocationType
from survey.models.interviewer import Interviewer

class Survey(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=True, unique=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    sample_size = models.PositiveIntegerField(max_length=2, null=False, blank=False, default=10)
    has_sampling = models.BooleanField(default=True)
    preferred_listing = models.ForeignKey('Survey', related_name='householdlist_users',
                                          help_text='Select which survey household listing to reuse. Leave empty for fresh listing', required=False)

    # min_percent_reg_houses = models.IntegerField(verbose_name='Min % Of Registered Households', default=80, validators=[MinValueValidator(0), MaxValueValidator(100)],
    #                                                     help_text='Enter minimum percentage of total household to be registered before survey can start on ODK channel')


    class Meta:
        app_label = 'survey'
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

    def generate_completion_report(self, batch=None):
        data = []
        all_interviewers = Interviewer.objects.all()
        for interviewer in all_interviewers:
            if interviewer.completed_batch_or_survey(self, batch=batch):
                row = [interviewer.name, ','.join(interviewer.access_ids)]
                if interviewer.ea:
                    row.extend(interviewer.locations_in_hierarchy().values_list('name', flat=True))
                data.append(row)
        return data

    def batches_enabled(self, ea=None):
        if ea:
            return self.commencement_registry.filter(ea=ea).exists()
        return self.commencement_registry.exists()

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

class SurveySampleSizeReached(Exception):
    pass

class BatchCommencement(BaseModel):
    survey = models.ForeignKey(Survey, null=True, related_name='commencement_registry')
    ea = models.ForeignKey('EnumerationArea', null=True, related_name='commencement_registry')

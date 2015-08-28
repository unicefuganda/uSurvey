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
    min_percent_reg_houses = models.IntegerField(verbose_name='Min % Of Registered Households', default=80, validators=[MinValueValidator(0), MaxValueValidator(100)],
                                                        help_text='Enter minimum percentage of total household to be registered before survey can start on ODK channel')


    class Meta:
        app_label = 'survey'
        
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
        header = ['Interviewer', 'Access Channels']
        header.extend(LocationType.objects.all().values_list('name', flat=True))
        data = [header]
        all_interviewers = Interviewer.objects.all()
        # import pdb; pdb.set_trace()
        for interviewer in all_interviewers:
            if interviewer.present_households(self).count() and interviewer.completed_batch_or_survey(self, batch):
                row = [interviewer.name, ','.join(interviewer.access_ids)]
                if interviewer.ea:
                    row.extend(interviewer.locations_in_hierarchy().values_list('name', flat=True))
                data.append(row)
        return data
        
class SurveySampleSizeReached(Exception):
    pass
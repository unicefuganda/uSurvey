from django.db import models
from survey.models.base import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator

class Survey(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=True, unique=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    sample_size = models.PositiveIntegerField(max_length=2, null=False, blank=False, default=10)
    type = models.BooleanField(default=False)
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
        
class SurveySampleSizeReached(Exception):
    pass
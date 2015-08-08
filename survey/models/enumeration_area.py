# from rapidsms.contrib.locations.models import Location
from survey.models.locations import Location
from survey.models import BaseModel
from django.db import models
from survey.models.surveys import Survey
from survey.models.batch import Batch, BatchLocationStatus

class EnumerationArea(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=True)
    total_households = models.PositiveIntegerField(null=True, blank=True)
    locations = models.ManyToManyField(Location, null=True, related_name="enumeration_areas")

    def __unicode__(self):
        return self.name
   
    def open_surveys(self):
        location_registry =  BatchLocationStatus.objects.filter(location__in=self.locations.all())
        return Survey.objects.filter(pk__in=[reg.batch.survey.pk for reg in location_registry])
    
    def open_batches(self, survey):
        location_registry =  BatchLocationStatus.objects.filter(location__in=self.locations.all())
        return Batch.objects.filter(pk__in=[reg.batch.pk for reg in location_registry], survey=survey).order_by('order')
        
#     def validate_unique(self, *args, **kwargs):
#         super(EnumerationArea, self).validate_unique(*args, **kwargs)
#         
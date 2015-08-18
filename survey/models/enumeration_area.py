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
        return list(Survey.objects.filter(pk__in=[reg.batch.survey.pk for reg in location_registry]))
    
    def open_batches(self, survey, house_member=None):
        location_registry =  BatchLocationStatus.objects.filter(location__in=self.locations.all())
        batches = list(survey.batches.filter(pk__in=[reg.batch.pk for reg in location_registry]).order_by('order'))
        if house_member is not None:
            applicable = []
            for batch in batches:
                if batch.is_applicable(house_member):
                   applicable.append(batch)
            batches = applicable
        return batches
        
            
        
#     def validate_unique(self, *args, **kwargs):
#         super(EnumerationArea, self).validate_unique(*args, **kwargs)
#         
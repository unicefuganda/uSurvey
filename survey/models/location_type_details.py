from django.db import models
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import BaseModel


class LocationTypeDetails(BaseModel):
    required = models.BooleanField(default=False, verbose_name='required')
    has_code = models.BooleanField(default=False, verbose_name='has code')
    code = models.CharField(max_length=30, blank=True, null=True)
    location_type = models.ForeignKey(LocationType, null=False, related_name="details")
    country = models.ForeignKey(Location, null=True, related_name="details")
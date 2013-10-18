from django.db import models
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import BaseModel


class LocationTypeDetails(BaseModel):
    required = models.BooleanField(default=False)
    has_code = models.BooleanField(default=False)
    code = models.CharField(max_length=30, blank=True, null=True)
    location_type = models.ForeignKey(LocationType, null=False, related_name="details")
    country = models.ForeignKey(Location, null=True, related_name="details")
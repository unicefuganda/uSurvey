from django.db import models
from rapidsms.contrib.locations.models import LocationType
from survey.models import BaseModel


class LocationTypeDetails(BaseModel):
    required = models.BooleanField(default=True)
    has_code = models.BooleanField(default=False)
    code = models.CharField(max_length=30, blank=True, null=True)
    location_type = models.ForeignKey(LocationType, null=False, related_name="details")
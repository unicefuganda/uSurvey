from rapidsms.contrib.locations.models import Location
from survey.models import BaseModel
from django.db import models


class EnumerationArea(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=True)
    survey = models.ForeignKey("Survey", null=True, related_name="enumeration_area")
    locations = models.ManyToManyField(Location, null=True, related_name="locations")
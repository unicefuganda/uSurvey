# from rapidsms.contrib.locations.models import Location
from survey.models.locations import Location
from survey.models import BaseModel
from django.db import models


class EnumerationArea(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=True)
    total_households = models.PositiveIntegerField(null=True, blank=True)
    locations = models.ManyToManyField(Location, null=True, related_name="enumeration_area")

    def __unicode__(self):
        return self.name

    
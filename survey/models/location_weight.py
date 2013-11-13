from rapidsms.contrib.locations.models import Location
from django.db import models
from survey.models.base import BaseModel


class LocationWeight(BaseModel):
    location = models.ForeignKey(Location, null=False, related_name='weight')
    survey = models.ForeignKey('Survey', null=False, related_name='location_weight')
    selection_probability = models.FloatField(null=False, default=1.0)
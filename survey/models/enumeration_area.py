from rapidsms.contrib.locations.models import Location
from survey.models import BaseModel
from django.db import models


class EnumerationArea(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=True)
    survey = models.ForeignKey("Survey", null=True, related_name="enumeration_area")
    total_households = models.PositiveIntegerField(default=1)
    locations = models.ManyToManyField(Location, null=True, related_name="enumeration_area")

    def __unicode__(self):
        return self.name

    def parent_location(self):
        location = self.locations.all()[0]
        from survey.models import LocationTypeDetails
        second_lowest_level_type = LocationTypeDetails.get_second_lowest_level_type()
        return location.get_ancestors().filter(type=second_lowest_level_type)[0]

    def get_siblings(self):
        return self.under_(self.parent_location())

    @classmethod
    def under_(cls, selected_location):
        return cls.objects.filter(locations__in=selected_location.get_descendants()).distinct('name', 'survey')
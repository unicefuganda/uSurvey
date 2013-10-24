from django.db import models
from django.db.models import Max
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import BaseModel


class LocationTypeDetails(BaseModel):
    required = models.BooleanField(default=False, verbose_name='required')
    has_code = models.BooleanField(default=False, verbose_name='has code')
    length_of_code = models.PositiveIntegerField(max_length=10, blank=True, null=True)
    location_type = models.ForeignKey(LocationType, null=False, related_name="details")
    country = models.ForeignKey(Location, null=True, related_name="details")
    order = models.PositiveIntegerField(unique=True,blank=True,null=True)

    @classmethod
    def get_ordered_types(cls):
        return LocationType.objects.all().order_by('details__order')

    def save(self, *args, **kwargs):
        last_order = LocationTypeDetails.objects.aggregate(Max('order'))['order__max']
        self.order = last_order + 1 if last_order else 1
        super(LocationTypeDetails, self).save(*args, **kwargs)
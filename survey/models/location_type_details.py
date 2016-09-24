from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Max
from survey.models.locations import LocationType, Location
from survey.models import BaseModel


class LocationTypeDetails(BaseModel):
    INITIAL_ORDER = 0
    ONE = 1

    required = models.BooleanField(default=False, verbose_name='required')
    has_code = models.BooleanField(default=False, verbose_name='has code')
    length_of_code = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], blank=True,
                                                 null=True)
    location_type = models.ForeignKey(
        LocationType, null=False, related_name="details")
    country = models.ForeignKey(Location, null=True, related_name="details")
    order = models.PositiveIntegerField(unique=True, blank=True, null=True)

    @classmethod
    def get_ordered_types(cls):
        return LocationType.objects.all().order_by('details__order')

    def save(self, *args, **kwargs):
        last_order = LocationTypeDetails.objects.aggregate(
            Max('order'))['order__max'] or self.INITIAL_ORDER
        if not self.order:
            self.order = last_order + self.ONE
        super(LocationTypeDetails, self).save(*args, **kwargs)

    @classmethod
    def the_country(cls):
        all_types_details = cls.objects.all().exclude(country=None)
        if all_types_details.exists():
            return all_types_details[0].country
        return None

    @classmethod
    def get_second_lowest_level_type(cls):
        return cls.objects.all().order_by('-order')[1].location_type

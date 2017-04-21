# from rapidsms.contrib.locations.models import Location
from survey.models.locations import Location
from survey.models import BaseModel
from django.db import models
from survey.models.surveys import Survey
from survey.models.batch import BatchLocationStatus


class EnumerationArea(BaseModel):
    name = models.CharField(
        max_length=200,
        blank=False,
        null=True,
        db_index=True)
    code = models.CharField(max_length=200, editable=False,
                            blank=True, null=True, unique=True)
    # total_households = models.PositiveIntegerField(null=True, blank=True)
    locations = models.ManyToManyField(
        Location, related_name="enumeration_areas", db_index=True)

    def __unicode__(self):
        return self.name

    def parent_locations(self):
        # now this assumes ea locations are made from smallest units belonging
        # to same group
        if self.locations.exists():
            location = self.locations.all()[0]
            return location.get_ancestors().exclude(parent__isnull=True)

    def get_survey_openings(self, survey=None):
        parent_locations = set()
        ea_locations = self.locations.all()
        if ea_locations:
            map(lambda loc: parent_locations.update(
                loc.get_ancestors(include_self=True)), ea_locations)
        kwargs = {'location__pk__in': [loc.pk for loc in parent_locations]}
        if survey:
            kwargs['batch__survey'] = survey
        location_registry = BatchLocationStatus.objects.filter(**kwargs)
        return location_registry

    def open_surveys(self):
        location_registry = self.get_survey_openings()
        return list(
            Survey.objects.filter(
                pk__in=[
                    reg.batch.survey.pk for reg in location_registry]))

    def open_batches(self, survey, access_channel=None):
        location_registry = self.get_survey_openings(survey)
        batches = list([reg.batch for reg in location_registry])
        return sorted(batches, key=lambda batch: batch.order)

    def get_siblings(self):
        return self.under_(self.parent_location())

    @classmethod
    def under_(cls, selected_location):
        return cls.objects.filter(
            locations__in=selected_location.get_leafnodes()).distinct('name')

#     def validate_unique(self, *args, **kwargs):
#         super(EnumerationArea, self).validate_unique(*args, **kwargs)
#
